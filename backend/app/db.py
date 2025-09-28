import asyncio
from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from typing import Any, Dict


async def main():
    uri = "mongodb+srv://cheech976:James1996@cluster0.kvrql.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client: AsyncMongoClient[Dict[str, Any]] = AsyncMongoClient(
        uri, server_api=ServerApi("1", strict=True, deprecation_errors=True)
    )

    try:
        database = client.get_database("myNHL")
        players = database.get_collection("players")

        # Query for a movie that has the title 'Back to the Future'
        query = {"playerInfo.playerId": 8479983}
        player = await players.find_one(query)

        print(player)

        await client.close()

    except Exception as e:
        raise Exception("Unable to find the document due to the following error: ", e)


# Run the async function
asyncio.run(main())
