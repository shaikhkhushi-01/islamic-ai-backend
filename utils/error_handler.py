from fastapi import HTTPException


def server_error(e):

    raise HTTPException(

        status_code=500,

        detail=str(e)

    )
