# Database Management Tools

This directory contains comprehensive database management tools integrated into the Docker workflow.

## 📁 New Scripts Added

### 1. `restore_database.py`
**Standalone comprehensive database restoration script**
- ✅ Automatic backup of current database before restore
- ✅ Backup file integrity verification
- ✅ JSON corruption detection and repair
- ✅ Task count synchronization fix
- ✅ Database restoration with proper permissions
- ✅ Post-restore verification
- ✅ Frontend restart for UI refresh

**Usage:**
```bash
python docker/restore_database.py /path/to/backup.db
```

### 2. `database_restore_verification.py`
**Standalone database verification and analysis script**
- ✅ Database integrity checks
- ✅ Task count validation and repair
- ✅ JSON format validation and repair
- ✅ Table relationship verification
- ✅ Comprehensive database summary

**Usage:**
```bash
python docker/database_restore_verification.py /path/to/database.db
```

### 3. `backup_verification.py`
**Backup file verification and repair script**
- ✅ Detects and repairs JSON double-encoding corruption
- ✅ Creates pre-repair backups
- ✅ Validates backup integrity

**Usage:**
```bash
python docker/backup_verification.py /path/to/backup.db
```

## 🔧 Integration with mcp-docker.py

The main Docker management script has been enhanced with **two new menu options**:

### **"Restore Database (Advanced)"**
- Comprehensive database restoration with full verification
- Automatically backs up current database
- Repairs all common issues (JSON corruption, task counts)
- Restarts frontend to display restored data
- **Recommended for all database restoration needs**

### **"Verify Database"**  
- Checks and repairs database without restoration
- Fixes task count discrepancies
- Repairs JSON corruption in subtasks
- Validates database integrity
- **Use when experiencing data display issues**

## 🚀 Updated Workflow

### Via run_docker.sh (Recommended)
```bash
# Normal interactive mode with new database tools
./run_docker.sh

# Development mode (unchanged)
./run_docker.sh --dev
```

### Direct mcp-docker.py Access
```bash
# Activate environment and run Docker manager
source .venv/bin/activate
python dhafnck_mcp_main/docker/mcp-docker.py
```

## 🔍 Common Use Cases

### 1. **Database Restore After Backup**
1. Run `./run_docker.sh`
2. Select "Restore Database (Advanced)"
3. Provide path to backup file
4. Script handles everything automatically

### 2. **Fix "0 tasks" Display Issue**
1. Run `./run_docker.sh`
2. Select "Verify Database"
3. Script fixes task count synchronization

### 3. **Repair JSON Corruption**
Both "Restore Database (Advanced)" and "Verify Database" automatically detect and repair:
- Double-encoded JSON in subtask assignees
- Invalid assignee format
- Task count mismatches

## ✅ What Was Fixed

1. **Task Count Synchronization**: Branches now show correct task counts
2. **JSON Corruption**: Subtask assignees display properly (not "[" "]")
3. **Database Restoration**: Complete verification and repair workflow
4. **Frontend Refresh**: UI automatically updates after database changes
5. **Permission Issues**: Automatic database permission fixing
6. **Backup Integrity**: Verification before restoration

## 🛡️ Safety Features

- **Automatic Backups**: Current database always backed up before restoration
- **Integrity Verification**: All databases verified before and after operations
- **Rollback Capability**: Original database preserved in case of issues
- **Permission Management**: Automatic fix of container permission issues
- **Error Recovery**: Comprehensive error handling and recovery procedures

## 📋 Integration Status

- ✅ **restore_database.py**: Integrated into mcp-docker.py menu
- ✅ **database_restore_verification.py**: Functions integrated into mcp-docker.py
- ✅ **backup_verification.py**: Available as standalone tool
- ✅ **run_docker.sh**: No changes needed (delegates to mcp-docker.py)
- ✅ **Menu Options**: Two new options added to Docker management interface
- ✅ **Error Handling**: Comprehensive error handling integrated
- ✅ **Documentation**: Complete usage documentation provided

The database management tools are now fully integrated into the Docker workflow and ready for production use.