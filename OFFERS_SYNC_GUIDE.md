# Cuelinks Offers Sync Service

## Overview

This service automatically fetches offers from the Cuelinks API, processes them, and stores them in the database with embeddings for enhanced search capabilities. It includes both manual and automatic scheduling features.

## Features

### 🔄 Automatic Daily Sync
- Runs daily at a configurable time (default: 2:00 AM)
- Fetches all available offers from Cuelinks API
- Processes and stores data with embeddings
- Tracks sync history and performance

### 🎯 Manual Sync Options
- Immediate sync via API endpoints
- Background sync for non-blocking operations
- Option to clear existing data or append new data
- Real-time status monitoring

### 📊 Smart Data Processing
- Automatic campaign and offer processing
- Text embedding generation for AI-powered search
- Category and metadata extraction
- HTML content cleaning

### 📈 Monitoring & Analytics
- Sync history tracking
- Performance metrics
- Error logging and reporting
- Admin dashboard for control

## Quick Start

### 1. Start the Application
```bash
python main.py
```

### 2. Access Admin Interface
Visit: http://localhost:8000/admin/sync

### 3. Test API Connectivity
```bash
curl http://localhost:8000/api/offers-sync/test-api
```

### 4. Run Manual Sync
```bash
curl -X POST http://localhost:8000/api/offers-sync/sync-now
```

## API Endpoints

### Offers Sync Management

#### Test API Connectivity
```
GET /api/offers-sync/test-api
```
Tests connection to Cuelinks API and returns sample data.

#### Manual Sync (Immediate)
```
POST /api/offers-sync/sync-now
Body: {"clear_data": true}
```
Runs synchronous sync operation (blocks until complete).

#### Manual Sync (Background)
```
POST /api/offers-sync/manual-sync
Body: {"clear_data": true}
```
Starts sync operation in background.

#### Get Sync Status
```
GET /api/offers-sync/status
```
Returns database counts, last sync info, and system status.

#### Get Last Sync Info
```
GET /api/offers-sync/last-sync
```
Returns details about the most recent sync operation.

#### Get Sync History
```
GET /api/offers-sync/sync-history?limit=10
```
Returns history of sync operations.

#### Clear All Data
```
DELETE /api/offers-sync/clear-data
```
Removes all campaigns, offers, and embeddings data.

### Scheduler Management

#### Get Scheduler Status
```
GET /api/scheduler/status
```
Returns scheduler status and next sync time.

#### Start Scheduler
```
POST /api/scheduler/start
```
Starts the automatic daily scheduler.

#### Stop Scheduler
```
POST /api/scheduler/stop
```
Stops the automatic scheduler.

#### Restart Scheduler
```
POST /api/scheduler/restart
```
Restarts the scheduler with current settings.

#### Update Sync Time
```
PUT /api/scheduler/sync-time
Body: {"sync_time": "03:00"}
```
Updates the daily sync time (24-hour format).

#### Trigger Immediate Sync
```
POST /api/scheduler/trigger-now
```
Manually triggers a sync operation immediately.

## Database Schema

### New Tables

#### `offer_sync_logs`
Tracks sync operations and performance:
- `id`: Unique identifier
- `last_run_date`: When the sync was started
- `total_offers_retrieved`: Number of offers processed
- `status`: running, completed, failed
- `error_message`: Error details if failed
- `sync_type`: auto, manual, manual_immediate
- `execution_time_seconds`: How long the sync took

#### Enhanced `campaigns` Table
- Stores campaign information from Cuelinks
- Linked to offers via foreign keys

#### Enhanced `offers` Table
- Complete offer details from Cuelinks API
- Includes affiliate URLs, dates, and metadata

#### Enhanced `offer_embeddings` Table
- Stores vector embeddings for AI search
- Combines campaign, title, description, and other fields
- Supports semantic search capabilities

## Configuration

### Environment Variables
```env
CUELINKS_API_KEY=your_api_key_here
CUELINKS_BASE_URL=https://www.cuelinks.com/api/v2
DATABASE_HOST=your_db_host
DATABASE_PORT=5432
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
```

### Scheduler Settings
- **Default Sync Time**: 2:00 AM daily
- **Configurable**: Can be changed via API or admin interface
- **Automatic Restart**: Restarts after time changes

## Data Processing Flow

1. **API Fetch**: Retrieves offers from Cuelinks with pagination
2. **Data Cleaning**: Processes HTML content and extracts metadata
3. **Campaign Processing**: Creates or updates campaign records
4. **Offer Processing**: Stores offer details with relationships
5. **Embedding Generation**: Creates vector embeddings for search
6. **Logging**: Records sync performance and results

## Error Handling

- **API Failures**: Graceful handling with retries
- **Database Errors**: Transaction rollbacks and error logging
- **Embedding Failures**: Fallback to simple hash-based embeddings
- **Scheduler Errors**: Automatic restart and error reporting

## Monitoring

### Admin Dashboard Features
- **Real-time Status**: Current database counts and sync status
- **Scheduler Control**: Start/stop/restart scheduler
- **Manual Operations**: Test API, run sync, clear data
- **History View**: Recent sync operations with performance data
- **Error Reporting**: Failed sync details and error messages

### Performance Metrics
- **Execution Time**: How long each sync takes
- **Throughput**: Number of offers processed per minute
- **Success Rate**: Percentage of successful syncs
- **Data Growth**: Database size trends over time

## Testing

### Test Script
Run the included test script:
```bash
python test_sync_service.py
```

### Manual Testing
1. **Test API**: Use admin interface or curl commands
2. **Monitor Logs**: Check console output for detailed information
3. **Verify Data**: Query database to confirm data storage
4. **Test Scheduling**: Verify automatic operations work correctly

## Troubleshooting

### Common Issues

#### API Connection Errors
- Verify `CUELINKS_API_KEY` is correct
- Check network connectivity
- Ensure API rate limits are not exceeded

#### Database Connection Errors
- Verify database credentials in `.env`
- Ensure database server is accessible
- Check if required tables exist

#### Embedding Generation Errors
- Install required ML packages: `pip install sentence-transformers`
- Check available system memory
- Use fallback embedding if ML packages fail

#### Scheduler Not Running
- Check if process has permission to create threads
- Verify scheduler was started properly
- Look for error messages in logs

### Debug Mode
Enable debug logging by setting:
```env
DEBUG=True
```

## Best Practices

### Sync Frequency
- **Daily Sync**: Recommended for most use cases
- **Manual Sync**: Use for testing or urgent updates
- **Avoid Over-syncing**: Don't sync more than 2-3 times per day

### Data Management
- **Regular Cleanup**: Consider archiving old sync logs
- **Monitor Growth**: Keep track of database size
- **Backup Strategy**: Ensure regular database backups

### Performance Optimization
- **Off-peak Scheduling**: Run syncs during low-traffic hours
- **Resource Monitoring**: Watch CPU and memory usage
- **Database Indexing**: Ensure proper indexes for search performance

## Security Considerations

- **API Key Protection**: Keep Cuelinks API key secure
- **Database Security**: Use strong database credentials
- **Access Control**: Restrict admin interface access
- **Rate Limiting**: Respect Cuelinks API rate limits

## Future Enhancements

- **Incremental Sync**: Only sync changed offers
- **Multi-source Support**: Add support for other affiliate networks
- **Advanced Analytics**: Detailed performance dashboards
- **Notification System**: Email/SMS alerts for sync failures
- **API Versioning**: Support for newer Cuelinks API versions

## Support

For issues or questions:
1. Check the logs for error messages
2. Use the admin interface for troubleshooting
3. Run the test script to verify functionality
4. Review this documentation for configuration help
