from lotr_sdk.filters import fields


def test_filter_fragments() -> None:
    assert fields.name.eq("Frodo").to_fragment() == "name=Frodo"
    assert fields.name.ne("Sauron").to_fragment() == "name!=Sauron"
    assert fields.runtimeInMinutes.gt(120).to_fragment() == "runtimeInMinutes>120"
    assert fields.runtimeInMinutes.lte(180).to_fragment() == "runtimeInMinutes<=180"
    assert fields.name.include(["Frodo", "Aragorn"]).to_fragment() == "name=Frodo,Aragorn"
    assert fields.name.exclude(["Merry", "Pippin"]).to_fragment() == "name!=Merry,Pippin"
    assert fields.dialog.regex("Ring").to_fragment() == "dialog=/Ring/"
    assert fields.name.exists().to_fragment() == "name"
