from dataclasses import dataclass


@dataclass
class WegsegmentPuntLocatie:
    wegsegment_id: str
    puntlocatie_id: str
    afstand: float
    geometrie: dict
    eigenschappen: dict = None

    @classmethod
    def from_dict(cls, data: dict):
        properties = data.get('properties', {})
        return cls(
            wegsegment_id=properties.get('wegsegment_id', ''),
            puntlocatie_id=properties.get('puntlocatie_id', ''),
            afstand=properties.get('afstand', 0),
            geometrie=data.get('geometry', {}),
            eigenschappen=properties
        )
