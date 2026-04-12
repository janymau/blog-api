# apps/test/a.py
import asyncio
import time
import httpx

BASE_URL = "http://127.0.0.1:8000/api/stats/"


async def single_request(client: httpx.AsyncClient) -> tuple[int, float]:
    start = time.perf_counter()
    r = await client.get(BASE_URL)
    elapsed = time.perf_counter() - start
    return r.status_code, elapsed


async def run_load_test(total: int = 99999999, concurrency: int = 20000):
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(client):
        async with semaphore:
            return await single_request(client)

    print(f"Sending {total} requests ({concurrency} concurrent) to {BASE_URL}")

    async with httpx.AsyncClient(timeout=30) as client:
        results = await asyncio.gather(*[bounded(client) for _ in range(total)], return_exceptions=True)

    ok     = [r for r in results if isinstance(r, tuple) and r[0] == 200]
    errors = [r for r in results if isinstance(r, Exception)]
    non200 = [r for r in results if isinstance(r, tuple) and r[0] != 200]
    times  = [r[1] for r in ok]

    print(f"\n{'='*50}")
    print(f"  Total requests:     {total}")
    print(f"  ✓ Success (200):    {len(ok)}")
    print(f"  ✗ Non-200:          {len(non200)}")
    print(f"  ✗ Exceptions:       {len(errors)}")
    if times:
        avg = sum(times) / len(times)
        print(f"  Avg response time:  {avg*1000:.1f} ms")
        print(f"  Min response time:  {min(times)*1000:.1f} ms")
        print(f"  Max response time:  {max(times)*1000:.1f} ms")
        print(f"  Throughput:         {len(ok)/sum(times):.1f} req/s")
    if errors:
        print(f"\n  First error: {errors[0]}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(run_load_test(total=50, concurrency=5))