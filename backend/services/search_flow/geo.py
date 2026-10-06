from geoalchemy2 import Geography
from sqlalchemy import cast, func


def user_point(latitude: float, longitude: float):

    return cast(
        func.ST_SetSRID(
            func.ST_MakePoint(
                longitude,
                latitude,
            ),
            4326,
        ),
        Geography(
            geometry_type="POINT",
            srid=4326,
        ),
    )