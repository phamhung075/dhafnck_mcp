import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';

interface AuditEntry {
  id: string;
  timestamp: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: any;
  ip_address: string;
  user_agent: string;
  result: 'success' | 'failure' | 'partial';
}

interface AuditFilters {
  dateFrom: string;
  dateTo: string;
  user: string;
  action: string;
  result: string;
  resourceType: string;
}

interface AuditTrailViewerProps {
  auditEntries: AuditEntry[];
  onExportAudit: (filters: AuditFilters) => Promise<void>;
  onViewEntryDetails: (entryId: string) => void;
}

export function AuditTrailViewer({
  auditEntries,
  onExportAudit,
  onViewEntryDetails
}: AuditTrailViewerProps) {
  const [filters, setFilters] = useState<AuditFilters>({
    dateFrom: '',
    dateTo: '',
    user: '',
    action: '',
    result: 'all',
    resourceType: 'all'
  });
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [entriesPerPage] = useState(25);

  const filteredEntries = useMemo(() => {
    return auditEntries.filter(entry => {
      const matchesDateRange = (!filters.dateFrom || entry.timestamp >= filters.dateFrom) &&
                              (!filters.dateTo || entry.timestamp <= filters.dateTo);
      const matchesUser = !filters.user || entry.user_id.toLowerCase().includes(filters.user.toLowerCase());
      const matchesAction = !filters.action || entry.action.toLowerCase().includes(filters.action.toLowerCase());
      const matchesResult = filters.result === 'all' || entry.result === filters.result;
      const matchesResourceType = filters.resourceType === 'all' || entry.resource_type === filters.resourceType;
      
      return matchesDateRange && matchesUser && matchesAction && matchesResult && matchesResourceType;
    });
  }, [auditEntries, filters]);

  const paginatedEntries = useMemo(() => {
    const startIndex = (currentPage - 1) * entriesPerPage;
    return filteredEntries.slice(startIndex, startIndex + entriesPerPage);
  }, [filteredEntries, currentPage, entriesPerPage]);

  const totalPages = Math.ceil(filteredEntries.length / entriesPerPage);

  const uniqueResourceTypes = useMemo(() => {
    return Array.from(new Set(auditEntries.map(entry => entry.resource_type)));
  }, [auditEntries]);

  const uniqueActions = useMemo(() => {
    return Array.from(new Set(auditEntries.map(entry => entry.action)));
  }, [auditEntries]);

  const handleExportAudit = async () => {
    await onExportAudit(filters);
  };

  const clearFilters = () => {
    setFilters({
      dateFrom: '',
      dateTo: '',
      user: '',
      action: '',
      result: 'all',
      resourceType: 'all'
    });
    setCurrentPage(1);
  };

  const getResultBadgeVariant = (result: string) => {
    switch (result) {
      case 'success': return 'default';
      case 'failure': return 'destructive';
      case 'partial': return 'secondary';
      default: return 'outline';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getUserAgent = (userAgent: string) => {
    // Extract browser and OS info from user agent
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    return 'Unknown';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Audit Trail</h2>
        <Button onClick={handleExportAudit}>
          Export Report
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter audit entries by date, user, action, and result</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <label className="text-sm font-medium">From Date</label>
              <Input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium">To Date</label>
              <Input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium">User</label>
              <Input
                placeholder="User ID"
                value={filters.user}
                onChange={(e) => setFilters(prev => ({ ...prev, user: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Action</label>
              <select
                value={filters.action}
                onChange={(e) => setFilters(prev => ({ ...prev, action: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="">All Actions</option>
                {uniqueActions.map(action => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Resource Type</label>
              <select
                value={filters.resourceType}
                onChange={(e) => setFilters(prev => ({ ...prev, resourceType: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="all">All Types</option>
                {uniqueResourceTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Result</label>
              <select
                value={filters.result}
                onChange={(e) => setFilters(prev => ({ ...prev, result: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="all">All Results</option>
                <option value="success">Success</option>
                <option value="failure">Failure</option>
                <option value="partial">Partial</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={clearFilters} variant="outline" size="sm">
              Clear Filters
            </Button>
            <div className="text-sm text-gray-500 flex items-center">
              Showing {filteredEntries.length} of {auditEntries.length} entries
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Audit Entries</CardTitle>
          <CardDescription>Detailed log of system activities and operations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left p-3 text-sm font-medium text-gray-500">Timestamp</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-500">User</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-500">Action</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-500">Resource</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-500">Result</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-500">IP Address</th>
                  <th className="text-left p-3 text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedEntries.map(entry => (
                  <tr key={entry.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="p-3 text-sm text-gray-900">
                      {formatTimestamp(entry.timestamp)}
                    </td>
                    <td className="p-3 text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{entry.user_id}</div>
                        <div className="text-xs text-gray-500">{getUserAgent(entry.user_agent)}</div>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-gray-900">{entry.action}</td>
                    <td className="p-3 text-sm text-gray-900">
                      <div>
                        <div className="font-medium">{entry.resource_type}</div>
                        <div className="text-xs text-gray-500 truncate max-w-32" title={entry.resource_id}>
                          {entry.resource_id}
                        </div>
                      </div>
                    </td>
                    <td className="p-3 text-sm">
                      <Badge variant={getResultBadgeVariant(entry.result)}>
                        {entry.result}
                      </Badge>
                    </td>
                    <td className="p-3 text-sm text-gray-900 font-mono">{entry.ip_address}</td>
                    <td className="p-3 text-sm">
                      <Dialog open={selectedEntry?.id === entry.id} onOpenChange={(open) => !open && setSelectedEntry(null)}>
                        <DialogTrigger asChild>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => setSelectedEntry(entry)}
                          >
                            Details
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                          <DialogHeader>
                            <DialogTitle>Audit Entry Details</DialogTitle>
                            <DialogDescription>
                              Complete information for audit entry {entry.id}
                            </DialogDescription>
                          </DialogHeader>
                          {selectedEntry && (
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <div className="text-sm font-medium text-gray-500">Timestamp</div>
                                  <div className="text-sm">{formatTimestamp(selectedEntry.timestamp)}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">User ID</div>
                                  <div className="text-sm">{selectedEntry.user_id}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">Action</div>
                                  <div className="text-sm">{selectedEntry.action}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">Result</div>
                                  <Badge variant={getResultBadgeVariant(selectedEntry.result)}>
                                    {selectedEntry.result}
                                  </Badge>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">Resource Type</div>
                                  <div className="text-sm">{selectedEntry.resource_type}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">Resource ID</div>
                                  <div className="text-sm font-mono text-xs break-all">{selectedEntry.resource_id}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">IP Address</div>
                                  <div className="text-sm font-mono">{selectedEntry.ip_address}</div>
                                </div>
                                <div>
                                  <div className="text-sm font-medium text-gray-500">User Agent</div>
                                  <div className="text-xs text-gray-600 break-all">{selectedEntry.user_agent}</div>
                                </div>
                              </div>
                              
                              {selectedEntry.details && Object.keys(selectedEntry.details).length > 0 && (
                                <div>
                                  <div className="text-sm font-medium text-gray-500 mb-2">Additional Details</div>
                                  <div className="bg-gray-50 p-3 rounded-lg">
                                    <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                                      {JSON.stringify(selectedEntry.details, null, 2)}
                                    </pre>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredEntries.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No audit entries matching current filters
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center mt-4">
              <div className="text-sm text-gray-500">
                Page {currentPage} of {totalPages} ({filteredEntries.length} total entries)
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {auditEntries.filter(e => e.result === 'success').length}
            </div>
            <div className="text-sm text-gray-500">Successful Operations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-red-600">
              {auditEntries.filter(e => e.result === 'failure').length}
            </div>
            <div className="text-sm text-gray-500">Failed Operations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {auditEntries.filter(e => e.result === 'partial').length}
            </div>
            <div className="text-sm text-gray-500">Partial Operations</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">
              {new Set(auditEntries.map(e => e.user_id)).size}
            </div>
            <div className="text-sm text-gray-500">Unique Users</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}