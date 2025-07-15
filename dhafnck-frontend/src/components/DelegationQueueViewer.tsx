/**
 * DelegationQueueViewer Component
 * View and manage pending delegations with approval/rejection workflow
 */

import React, { useState, useCallback } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert } from './ui/alert';
import { Separator } from './ui/separator';
import {
  DelegationQueueViewerProps,
  PendingDelegation
} from '../types/context-delegation';

function DelegationQueueViewer({
  pendingDelegations,
  onApproveDelegation,
  onRejectDelegation,
  onViewDelegationDetails,
  userRole,
  queueStats
}: DelegationQueueViewerProps) {
  const [selectedDelegation, setSelectedDelegation] = useState<PendingDelegation | null>(null);
  const [showRejectDialog, setShowRejectDialog] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  // Filter delegations based on status
  const filteredDelegations = pendingDelegations.filter(delegation => {
    if (filter === 'all') return true;
    return delegation.status === filter;
  });

  // Handle approval
  const handleApprove = useCallback(async (delegationId: string) => {
    setLoading(prev => ({ ...prev, [delegationId]: true }));
    try {
      await onApproveDelegation(delegationId);
    } catch (error) {
      console.error('Failed to approve delegation:', error);
    } finally {
      setLoading(prev => ({ ...prev, [delegationId]: false }));
    }
  }, [onApproveDelegation]);

  // Handle rejection
  const handleReject = useCallback(async (delegationId: string) => {
    if (!rejectionReason.trim()) return;

    setLoading(prev => ({ ...prev, [delegationId]: true }));
    try {
      await onRejectDelegation(delegationId, rejectionReason);
      setShowRejectDialog(null);
      setRejectionReason('');
    } catch (error) {
      console.error('Failed to reject delegation:', error);
    } finally {
      setLoading(prev => ({ ...prev, [delegationId]: false }));
    }
  }, [onRejectDelegation, rejectionReason]);

  // Check if user can perform actions
  const canApprove = userRole === 'admin' || userRole === 'reviewer';
  const canReject = userRole === 'admin' || userRole === 'reviewer';

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Delegation Queue</h2>
          <p className="text-sm text-gray-600">
            {filteredDelegations.length} of {pendingDelegations.length} delegations
          </p>
        </div>
        
        {queueStats && (
          <div className="flex space-x-4 text-sm">
            <div>
              <span className="text-gray-500">Pending:</span>
              <span className="ml-1 font-medium">{queueStats.total_pending}</span>
            </div>
            <div>
              <span className="text-gray-500">Avg Time:</span>
              <span className="ml-1 font-medium">{queueStats.average_approval_time}h</span>
            </div>
            <div>
              <span className="text-gray-500">Rejection Rate:</span>
              <span className="ml-1 font-medium">{Math.round(queueStats.rejection_rate * 100)}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium">Filter by status:</span>
          {(['all', 'pending', 'approved', 'rejected'] as const).map(status => (
            <Button
              key={status}
              size="sm"
              variant={filter === status ? 'default' : 'outline'}
              onClick={() => setFilter(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              <Badge variant="secondary" className="ml-2">
                {status === 'all' 
                  ? pendingDelegations.length 
                  : pendingDelegations.filter(d => d.status === status).length
                }
              </Badge>
            </Button>
          ))}
        </div>
      </Card>

      {/* Role Access Notice */}
      {!canApprove && !canReject && (
        <Alert>
          <span>You have read-only access to the delegation queue. Contact an administrator for approval permissions.</span>
        </Alert>
      )}

      {/* Delegation List */}
      <div className="space-y-3">
        {filteredDelegations.length === 0 ? (
          <Alert>
            <span>No delegations found matching the current filter.</span>
          </Alert>
        ) : (
          filteredDelegations.map(delegation => (
            <DelegationCard
              key={delegation.delegation_id}
              delegation={delegation}
              onApprove={() => handleApprove(delegation.delegation_id)}
              onReject={() => setShowRejectDialog(delegation.delegation_id)}
              onViewDetails={() => onViewDelegationDetails(delegation.delegation_id)}
              loading={loading[delegation.delegation_id] || false}
              canApprove={canApprove}
              canReject={canReject}
              isSelected={selectedDelegation?.delegation_id === delegation.delegation_id}
              onSelect={() => setSelectedDelegation(delegation)}
            />
          ))
        )}
      </div>

      {/* Rejection Dialog */}
      {showRejectDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="p-6 max-w-md w-full mx-4">
            <h3 className="font-semibold mb-4">Reject Delegation</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Rejection Reason (Required)
                </label>
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Explain why this delegation is being rejected..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => handleReject(showRejectDialog)}
                  disabled={!rejectionReason.trim() || loading[showRejectDialog]}
                >
                  {loading[showRejectDialog] ? 'Rejecting...' : 'Reject'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowRejectDialog(null);
                    setRejectionReason('');
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Detailed View */}
      {selectedDelegation && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Delegation Details</h3>
          <DelegationDetails delegation={selectedDelegation} />
        </Card>
      )}
    </div>
  );
}

// Individual Delegation Card
function DelegationCard({
  delegation,
  onApprove,
  onReject,
  onViewDetails,
  loading,
  canApprove,
  canReject,
  isSelected,
  onSelect
}: {
  delegation: PendingDelegation;
  onApprove: () => void;
  onReject: () => void;
  onViewDetails: () => void;
  loading: boolean;
  canApprove: boolean;
  canReject: boolean;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'default';
      case 'approved': return 'default';
      case 'rejected': return 'destructive';
      default: return 'outline';
    }
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  return (
    <Card 
      className={`p-4 cursor-pointer transition-colors ${
        isSelected ? 'border-blue-500 bg-blue-50' : 'hover:border-gray-300'
      }`}
      onClick={onSelect}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <Badge variant={getStatusColor(delegation.status)}>
                {delegation.status}
              </Badge>
              {delegation.priority && (
                <Badge variant={getPriorityColor(delegation.priority) as any}>
                  {delegation.priority} priority
                </Badge>
              )}
              <Badge variant="outline">
                {delegation.source_level} → {delegation.target_level}
              </Badge>
            </div>
            <h4 className="font-medium">
              {delegation.delegation_data?.pattern_name || 'Unnamed Pattern'}
            </h4>
            <p className="text-sm text-gray-600 mt-1">
              {delegation.delegation_reason}
            </p>
          </div>
          
          <div className="text-right text-xs text-gray-500">
            <div>{delegation.created_by}</div>
            <div>{new Date(delegation.created_at).toLocaleDateString()}</div>
          </div>
        </div>

        {/* Pattern Details */}
        <div className="bg-gray-50 rounded p-3 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-gray-500">Source:</span>
              <span className="ml-1">{delegation.source_context.slice(0, 8)}...</span>
            </div>
            <div>
              <span className="text-gray-500">Pattern Type:</span>
              <span className="ml-1">{delegation.delegation_data?.pattern_type || 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        {delegation.status === 'pending' && (canApprove || canReject) && (
          <>
            <Separator />
            <div className="flex items-center justify-between">
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails();
                }}
              >
                View Details
              </Button>
              
              <div className="flex space-x-2">
                {canReject && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      onReject();
                    }}
                    disabled={loading}
                  >
                    Reject
                  </Button>
                )}
                {canApprove && (
                  <Button
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onApprove();
                    }}
                    disabled={loading}
                  >
                    {loading ? 'Approving...' : 'Approve'}
                  </Button>
                )}
              </div>
            </div>
          </>
        )}

        {/* Review Notes */}
        {delegation.review_notes && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <span className="text-sm font-medium text-yellow-800">Review Notes:</span>
            <p className="text-sm text-yellow-700 mt-1">{delegation.review_notes}</p>
          </div>
        )}
      </div>
    </Card>
  );
}

// Detailed Delegation View
function DelegationDetails({ delegation }: { delegation: PendingDelegation }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="font-medium mb-2">Basic Information</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Delegation ID:</span>
              <span className="font-mono">{delegation.delegation_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Status:</span>
              <Badge variant={delegation.status === 'pending' ? 'default' : 
                              delegation.status === 'approved' ? 'default' : 'destructive'}>
                {delegation.status}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Created:</span>
              <span>{new Date(delegation.created_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Created By:</span>
              <span>{delegation.created_by}</span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium mb-2">Delegation Flow</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Source Context:</span>
              <span className="font-mono">{delegation.source_context.slice(0, 12)}...</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Source Level:</span>
              <span>{delegation.source_level}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Target Level:</span>
              <span>{delegation.target_level}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Priority:</span>
              <span>{delegation.priority || 'Not set'}</span>
            </div>
          </div>
        </div>
      </div>

      <Separator />

      <div>
        <h4 className="font-medium mb-2">Pattern Information</h4>
        <div className="bg-gray-50 rounded p-4">
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Name:</span>
              <span className="ml-2">{delegation.delegation_data?.pattern_name || 'Not specified'}</span>
            </div>
            <div>
              <span className="font-medium">Type:</span>
              <span className="ml-2">{delegation.delegation_data?.pattern_type || 'Not specified'}</span>
            </div>
            <div>
              <span className="font-medium">Usage Guide:</span>
              <p className="mt-1 text-gray-700">{delegation.delegation_data?.usage_guide || 'No usage guide provided'}</p>
            </div>
            {delegation.delegation_data?.tags && delegation.delegation_data.tags.length > 0 && (
              <div>
                <span className="font-medium">Tags:</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {delegation.delegation_data.tags.map((tag: string, index: number) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <Separator />

      <div>
        <h4 className="font-medium mb-2">Delegation Reason</h4>
        <div className="bg-blue-50 border border-blue-200 rounded p-4">
          <p className="text-sm text-blue-800">{delegation.delegation_reason}</p>
        </div>
      </div>

      {delegation.delegation_data?.implementation && (
        <>
          <Separator />
          <div>
            <h4 className="font-medium mb-2">Implementation Details</h4>
            <div className="bg-gray-100 rounded p-4">
              <pre className="text-xs overflow-x-auto">
                {JSON.stringify(delegation.delegation_data.implementation, null, 2)}
              </pre>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export { DelegationQueueViewer };
export default DelegationQueueViewer;