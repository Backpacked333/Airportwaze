# Alembic Database Migrations

This directory contains database migration scripts for AirportWaze.

## Setup

Alembic is already configured and ready to use. The configuration is in `alembic.ini` at the project root.

## Environment Variables

Make sure your `.env` file contains:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/airportwaze
```

## Common Commands

### Apply migrations (upgrade to latest)
```bash
alembic upgrade head
```

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Rollback one migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current database version
```bash
alembic current
```

### Rollback to a specific version
```bash
alembic downgrade <revision_id>
```

### Upgrade to a specific version
```bash
alembic upgrade <revision_id>
```

## Initial Setup

The initial migration `001_initial_schema.py` creates:
- `users` table for authentication
- `wait_time_reports` table for crowdsourced data

To apply the initial schema:

```bash
alembic upgrade head
```

## Creating New Migrations

1. Make changes to your SQLAlchemy models in `app/models/`
2. Generate a new migration:
   ```bash
   alembic revision --autogenerate -m "Add new table/column"
   ```
3. Review the generated migration in `alembic/versions/`
4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

## Best Practices

- Always review auto-generated migrations before applying
- Test migrations on a development database first
- Keep migrations small and focused
- Write meaningful migration messages
- Never modify applied migrations - create new ones instead
- Always write both `upgrade()` and `downgrade()` functions

## Troubleshooting

### "Can't locate revision identified by..."
This usually means your database is out of sync. Check the current version:
```bash
alembic current
```

### Reset to clean state (DESTRUCTIVE)
```bash
alembic downgrade base
alembic upgrade head
```

### Manual SQL execution
If you need to run raw SQL:
```python
def upgrade():
    op.execute("CREATE INDEX idx_custom ON table_name (column)")
```

## Migration File Structure

Each migration file contains:
- `revision`: Unique identifier for this migration
- `down_revision`: Previous migration it depends on
- `upgrade()`: Function to apply changes
- `downgrade()`: Function to rollback changes

## Production Deployment

For production deployments:

1. Test migrations in staging environment
2. Backup database before applying
3. Apply migrations during maintenance window:
   ```bash
   alembic upgrade head
   ```
4. Verify application starts correctly
5. Monitor logs for any issues

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
