# Deployment Scripts

Scripts for starting and managing the Easy Local Chat server.

## Scripts

| Script | Description |
|--------|-------------|
| `start_server.sh` | Start production server |
| `start_server_dev.sh` | Start development server (auto-reload) |
| `stop_server.sh` | Stop server |
| `server_status.sh` | Check server status |

## Usage

**Start server:**
```bash
./deployment/start_server.sh
```

**Start development server:**
```bash
./deployment/start_server_dev.sh
```

**Stop server:**
```bash
./deployment/stop_server.sh
```

**Check status:**
```bash
./deployment/server_status.sh
```

## Notes

- Virtual environment is created automatically on first run
- Admin credentials are set on first startup
- Press `Ctrl+C` to stop the server

