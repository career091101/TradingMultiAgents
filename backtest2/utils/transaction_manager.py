"""Transaction manager for atomic operations"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import copy


logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class TransactionLog:
    """Log entry for a transaction"""
    transaction_id: str
    timestamp: datetime
    operation: str
    before_state: Dict[str, Any]
    after_state: Optional[Dict[str, Any]] = None
    status: TransactionStatus = TransactionStatus.PENDING
    error: Optional[str] = None
    
    
class TransactionContext:
    """Context for atomic transaction execution"""
    
    def __init__(self, transaction_id: str, operation: str):
        self.transaction_id = transaction_id
        self.operation = operation
        self.timestamp = datetime.now()
        self.rollback_actions: List[Callable] = []
        self.state_snapshots: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.TransactionContext")
        
    def add_rollback_action(self, action: Callable) -> None:
        """Add action to execute on rollback"""
        self.rollback_actions.append(action)
        
    def snapshot_state(self, key: str, state: Any) -> None:
        """Take snapshot of state for rollback"""
        self.state_snapshots[key] = copy.deepcopy(state)
        
    async def rollback(self) -> None:
        """Execute rollback actions in reverse order"""
        self.logger.warning(f"Rolling back transaction {self.transaction_id}")
        
        for action in reversed(self.rollback_actions):
            try:
                if asyncio.iscoroutinefunction(action):
                    await action()
                else:
                    action()
            except Exception as e:
                self.logger.error(f"Error during rollback: {e}")
                

class AtomicTransactionManager:
    """Manager for atomic transaction execution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.transaction_logs: List[TransactionLog] = []
        self.active_transactions: Dict[str, TransactionContext] = {}
        
        # Locks for different resources
        self.locks = {
            "cash": asyncio.Lock(),
            "positions": asyncio.Lock(),
            "portfolio": asyncio.Lock()
        }
        
        # Global lock for critical sections
        self.global_lock = asyncio.Lock()
        
    async def acquire_locks(self, resources: List[str]) -> List[asyncio.Lock]:
        """Acquire multiple locks in consistent order to prevent deadlocks"""
        # Sort resources to ensure consistent lock ordering
        sorted_resources = sorted(resources)
        acquired_locks = []
        
        try:
            for resource in sorted_resources:
                if resource in self.locks:
                    await self.locks[resource].acquire()
                    acquired_locks.append(self.locks[resource])
            return acquired_locks
        except Exception as e:
            # Release any acquired locks on error
            for lock in acquired_locks:
                lock.release()
            raise
            
    def release_locks(self, locks: List[asyncio.Lock]) -> None:
        """Release acquired locks"""
        for lock in locks:
            lock.release()
            
    async def execute_transaction(
        self,
        transaction_id: str,
        operation: str,
        execute_fn: Callable,
        resources: List[str],
        before_state: Dict[str, Any]
    ) -> Any:
        """Execute a transaction atomically"""
        
        context = TransactionContext(transaction_id, operation)
        self.active_transactions[transaction_id] = context
        
        # Create transaction log entry
        log_entry = TransactionLog(
            transaction_id=transaction_id,
            timestamp=context.timestamp,
            operation=operation,
            before_state=before_state
        )
        
        locks = []
        
        try:
            # Acquire necessary locks
            locks = await self.acquire_locks(resources)
            
            # Execute the transaction
            result = await execute_fn(context)
            
            # Mark as committed
            log_entry.status = TransactionStatus.COMMITTED
            log_entry.after_state = self._capture_after_state(before_state.keys())
            
            self.logger.info(f"Transaction {transaction_id} committed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transaction {transaction_id} failed: {e}")
            
            # Rollback
            try:
                await context.rollback()
                log_entry.status = TransactionStatus.ROLLED_BACK
            except Exception as rollback_error:
                self.logger.error(f"Rollback failed: {rollback_error}")
                log_entry.status = TransactionStatus.FAILED
                
            log_entry.error = str(e)
            raise
            
        finally:
            # Release locks
            self.release_locks(locks)
            
            # Record transaction log
            self.transaction_logs.append(log_entry)
            
            # Clean up
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
                
    def _capture_after_state(self, keys: Any) -> Dict[str, Any]:
        """Capture state after transaction (to be implemented by specific use case)"""
        # This would be implemented based on specific state requirements
        return {}
        
    async def execute_with_global_lock(self, fn: Callable) -> Any:
        """Execute function with global lock for critical sections"""
        async with self.global_lock:
            return await fn()
            
    def get_transaction_logs(
        self,
        status: Optional[TransactionStatus] = None,
        limit: Optional[int] = None
    ) -> List[TransactionLog]:
        """Get transaction logs with optional filtering"""
        logs = self.transaction_logs
        
        if status:
            logs = [log for log in logs if log.status == status]
            
        if limit:
            logs = logs[-limit:]
            
        return logs
        
    def clear_old_logs(self, keep_last: int = 1000) -> None:
        """Clear old transaction logs to prevent memory growth"""
        if len(self.transaction_logs) > keep_last:
            self.transaction_logs = self.transaction_logs[-keep_last:]