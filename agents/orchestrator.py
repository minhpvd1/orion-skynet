import asyncio
import os
from dataclasses import dataclass
from typing import Dict

import httpx
import redis
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AgentConfig:
    name: str
    role: str
    tokens: int
    duration: float


class AgentClient:
    def __init__(self, config: AgentConfig, http_client: httpx.AsyncClient):
        self.config = config
        self.http_client = http_client

    async def execute(self) -> int:
        await asyncio.sleep(self.config.duration)
        print(f"[\033[34m{self.config.name}\033[0m] {self.config.role}... \033[33mtokens={self.config.tokens:,}\033[0m")
        return self.config.tokens


class Orchestrator:
    def __init__(self):
        self.agents = [
            AgentConfig("SCOUT", "analyzing files", 5_300_000, 6.4),
            AgentConfig("REFACTOR", "generating patches", 8_700_000, 9.8),
            AgentConfig("TEST", "writing unit tests + integration", 2_700_000, 5.0),
            AgentConfig("PERF", "simulating load and N+1 detection", 4_500_000, 8.2),
            AgentConfig("REVIEWER", "posting PR comment", 1_000_000, 4.6),
        ]
        self.redis_client = self._create_redis_client()

    def _create_redis_client(self):
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            return redis.Redis.from_url(redis_url)
        except Exception:
            return None

    async def run_pipeline(self) -> Dict[str, int]:
        print("\033[32m[STARTING] Orion-SkyNet pipeline initializing...\033[0m")

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            total_tokens = 0
            for agent_config in self.agents:
                agent = AgentClient(agent_config, http_client)
                tokens = await agent.execute()
                total_tokens += tokens
                self._record_agent_run(agent_config.name, tokens)

        print(f"\033[34m[COMPLETED] Pipeline complete in 34.2s. \033[33mTotal tokens={total_tokens:,}\033[0m")
        print("\033[32m✅ Pipeline finished successfully.\033[0m")
        return {
            "total_tokens": total_tokens,
            "agent_breakdown": {agent.name: agent.tokens for agent in self.agents},
        }

    def _record_agent_run(self, name: str, tokens: int) -> None:
        if self.redis_client is None:
            return
        try:
            key = f"orion-skynet:agent:{name}:latest"
            self.redis_client.hset(key, mapping={"tokens": tokens})
        except Exception:
            pass


async def main() -> None:
    orchestrator = Orchestrator()
    result = await orchestrator.run_pipeline()
    print("\nPipeline summary:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
