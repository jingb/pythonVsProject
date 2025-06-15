import asyncio
import aiohttp
import time

async def download_one(url): 
    session = aiohttp.ClientSession()
    async with session.get(url) as resp: 
        print('httpcode {} Read {} from {}'.format(resp.status, resp.content_length, url))
    await session.close()    
    # async with aiohttp.ClientSession() as session: 
    #     async with session.get(url) as resp: 
    #         print('httpcode {} Read {} from {}'.format(resp.status, resp.content_length, url))


async def download_all(sites): 
    tasks = [asyncio.create_task(download_one(site)) for site in sites] 
    await asyncio.gather(*tasks)


def main():
    sites = [
        'https://www.qq.com',
        'https://www.baidu.com']
    start_time = time.perf_counter()
    asyncio.run (download_all(sites))
    end_time = time.perf_counter ()
    print('Download {} sites in {} seconds'.format(len(sites), end_time - start_time))


if __name__ == '__main__':
    main()