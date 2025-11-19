import asyncio
from typing import Any, Dict, List


class SemaphoreService:
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(self, function: callable, user_data: Dict):
        async with self.semaphore:
            return await function(user_data)

    async def process_concurrently(self, users: List[Dict], function: callable) -> List[Dict[str, Any]]:
        """Process users in batches to respect concurrency limits."""
        tasks = [self.process_with_semaphore(
            function=function, user_data=user) for user in users]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'user_id': users[i]['id'],
                    'user': users[i]['email'],
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        return processed_results
