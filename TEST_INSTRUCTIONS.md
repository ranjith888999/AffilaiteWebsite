# How to Test the Chat Search Improvements

This guide explains how to test the improvements made to the chat search functionality, specifically the ability to search by campaign name.

## Prerequisites

- Make sure your database has been migrated with the new schema
- Verify the migration was successful
- If needed, run the embeddings rebuild script to update embeddings with campaign information
- Make sure your environment variables are set correctly

## Migration and Verification

Before testing, ensure your data is properly migrated:

1. Run the database management utility:
   ```bash
   ./manage_database.bat
   ```

2. Choose option 1 to migrate your database
3. When prompted, choose to verify the migration
4. If verification shows any issues, you may need to reset and rebuild the database (option 2)
5. After migration, rebuild the embeddings (option 3)

## Testing Options

### Option 1: Run the Service Tests (No Server Needed)

This tests the search service directly without requiring the server to be running:

```bash
python scripts/test_campaign_search.py
```

The test will:
- Run searches for multiple campaign names (Nykaa, Amazon, Myntra, etc.)
- Display the results and verify campaign names are included
- Test that the ultra_fast_service is finding offers by campaign name

### Option 2: Run Comprehensive Tests (Server Required)

This tests both the service layer and the API endpoint:

```bash
# First start the server in one terminal
python main.py

# Then in another terminal, run the comprehensive test
python scripts/test_chat_comprehensive.py
```

The comprehensive test will:
- Test the underlying search services directly
- Test the API endpoint by making HTTP requests
- Verify that campaign names are included in the search results

### Option 3: Use the Test Runner

For convenience, you can use the test runner script:

```bash
./run_tests.bat
```

This provides a menu to:
1. Test the campaign search service (no server needed)
2. Run the comprehensive test (server must be running)
3. Run the server in test mode

### Option 4: Manual Testing in the UI

For a complete end-to-end test, you can also:

1. Start the server: `python main.py`
2. Open your browser to http://localhost:8000/chat
3. Try searching for specific campaign names like:
   - "Show me Nykaa offers"
   - "Find Amazon deals"
   - "What are the best Myntra coupons?"

## Expected Results

After the changes, the chat system should:

1. Return relevant offers when users mention campaign names (e.g., "Nykaa offers")
2. Include campaign names in the search results
3. Provide more accurate results by searching across both offer descriptions and campaign names

## Troubleshooting

If the tests don't yield the expected results:

1. Check that the database migration was successful using the verification option
2. Verify that campaigns have proper names in the database
3. Verify that the embeddings have been rebuilt with campaign information
4. Make sure your database contains some offers with the campaign names you're testing
5. Check for any errors in the server logs

## Next Steps

If the tests are successful, consider:

1. Adding more tests for different search scenarios
2. Optimizing the search queries further
3. Adding more specific indexes to improve performance
4. Implementing full-text search in PostgreSQL for even better results
