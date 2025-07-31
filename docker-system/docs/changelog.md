# Docker System Changelog

All notable changes to the Docker System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Monitoring Dashboard Container Detection** (2025-07-20)
  - Fixed monitoring script to correctly detect actual running containers
  - Backend service now properly maps to `dhafnck-mcp-server` container instead of non-existent `dhafnck-backend`
  - Logs section now uses correct backend container name, eliminating "No such container" errors
  - Added network fallback detection: tries `dhafnck-network` first, falls back to `docker_default`
  - Service status now correctly shows backend as "Running" instead of "Stopped"
  - Network status now displays accurate container count (3 containers)
  - Postgres service correctly shows as "Stopped" when using SQLite mode
  - Resource usage section now displays proper container names and statistics

### Added
- **Comprehensive TDD Test Suite** (2025-07-20)
  - Added 16 comprehensive test cases for monitoring functionality in `tests/test_monitoring_container_names.sh`
  - Test coverage includes container detection, service status mapping, network monitoring, logs access, and resource usage
  - Implemented full Test-Driven Development workflow with proper commit separation
  - Mock Docker environment for isolated testing
  - Automated test validation for all monitoring features

### Technical Details
- **Container Mapping Implementation**: Added service-to-container name mapping logic in `lib/monitoring.sh`
- **Network Detection Resilience**: Implemented fallback network inspection for different Docker Compose configurations
- **Graceful Error Handling**: Enhanced error handling for missing containers and networks
- **Test Infrastructure**: Created comprehensive mock Docker environment for reliable testing

### Impact
- Monitoring dashboard now accurately reflects actual system state
- Eliminates confusing "Stopped" status for running services
- Provides reliable real-time system monitoring
- Improved debugging capabilities with correct log access
- Enhanced user experience with accurate service status information

---

## Guidelines for Future Entries

### Categories
- **Added** for new features
- **Changed** for changes in existing functionality  
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

### Format
```markdown
## [Version] - YYYY-MM-DD
### Category
- Brief description of change
  - Technical details if needed
  - Impact on users
```

### Commit Reference
All changelog entries should reference the actual Git commits that implement the changes.