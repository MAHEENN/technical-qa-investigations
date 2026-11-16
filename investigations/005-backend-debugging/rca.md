# Root Cause Analysis: Customer Email Update Did Not Persist

**Project:** Local Python Customer API  
**Environment:** Local development  
**Validation status:** Two `unittest` integration tests reported passing.

## Incident Summary

A request to `PUT /api/customers/4821` returned HTTP `200` with a success response, but a subsequent GET for the same customer returned `old@example.com` instead of the requested `new@example.com`.

The `update_customer` function modified a shallow copy of the customer dictionary without writing the changed value back to the stored dictionary. As a result, the response indicated success while the API's in-memory state remained unchanged.

## Reproduction

1. Start the local API with customer `4821` having the email `old@example.com`.
2. Send `PUT /api/customers/4821` with the JSON body:

   ```json
   { "email": "new@example.com" }
   ```

3. Observe the HTTP `200` success response.
4. Send `GET /api/customers/4821`.
5. Observe that the returned email is still `old@example.com`.

## Expected and Actual Behavior

| Aspect | Expected | Actual |
| --- | --- | --- |
| Stored email after a valid update | `new@example.com` | `old@example.com` |
| Subsequent GET response | Returns the updated email | Returns the original email |
| PUT response | Reports success after updating the stored customer | Reports success despite leaving the stored customer unchanged |

## Debugger Evidence

Debugger observations after the email assignment:

```python
customer['email']                      # 'new@example.com'
customers[4821]['email']               # 'old@example.com'
customer is customers[4821]            # False
```

The local variable contained the new value, while the dictionary used as the API's data store retained the old value. The identity check confirmed that the local variable and stored customer were different dictionary objects.

## Primary Root Cause

The update logic followed this pattern:

```python
customer = customers[customer_id].copy()
customer['email'] = email
```

`dict.copy()` creates a new, shallow dictionary. Assigning a new value to the copy's top-level `email` key changes only that copy. It does not replace the corresponding value in `customers[customer_id]`.

The function neither modified the stored customer directly nor assigned the modified copy back to the store. The state change therefore existed only in the local copy.

## Contributing Factor: Misleading Success Response

The function completed without raising an error and returned HTTP `200`, even though the intended state change had not occurred in the store. The success response alone was therefore insufficient evidence that the update worked.

This made the defect easy to miss when checking only the PUT status or response body. Reading the customer again exposed the mismatch between the response and stored state.

## Fix

Update the stored customer dictionary directly after the request has passed the applicable validation:

```python
customers[customer_id]['email'] = email
```

This changes the dictionary that subsequent GET requests read. The snippet illustrates the corrected assignment; it is not a complete endpoint implementation.

## Regression Tests

Two `unittest` integration tests were reported passing:

1. **Email update persistence:** Update a customer's email through the API, then retrieve the customer and assert that the returned email matches the new value. This checks the observable state change across requests and would detect the original copy-related defect.
2. **Invalid email type:** Submit an email value of an invalid type and assert that the API returns HTTP `400`. This covers input type validation, a separate concern from the persistence defect.

The reported results cover these two scenarios; they do not establish complete endpoint coverage.

## Limitations

- The data store is an in-memory Python dictionary, not a database.
- Here, “persistence” means that an update remains available to subsequent requests using the same in-memory store. It does not imply durability across application restarts or consistency across multiple worker processes.
- The reported tests cover the two behaviors described above. They do not establish concurrency safety, database behavior, or comprehensive email validation.

## Follow-up

- Keep both regression tests in the project and run them after changes to customer update logic.
- Ensure each test starts with known customer data so results do not depend on test order.
- Add coverage for an unknown customer ID and confirm that rejected updates leave stored data unchanged.
- Document the in-memory storage limitation in the project README. If a database is introduced later, add tests that verify committed updates through the database-backed API.

## Learning

A successful HTTP response does not prove that an intended state change occurred. Verify update behavior with a subsequent read, and use debugger values and object identity checks to distinguish changes to a copy from changes to the actual store.
