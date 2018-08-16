from opentrons.config import get_config_index
from opentrons.data_storage import serializers as ser
from opentrons.data_storage import labware_definitions as ldef
from opentrons.data_storage import database as sqldb

test_defn_root = get_config_index().get('labware').get('baseDefinitionDir')


# ===================
# Tests below are compatibility tests with sqlite database. These tests will no
# longer be relevant once the sqlite database is removed, and should be revised
# or deleted
# ===================
def test_one_deserializer():
    plate = '6-well-plate'
    new_container = ser.json_to_container(
        ldef._load_definition(test_defn_root, plate))
    old_container = sqldb.load_container(plate)

    old_wells = {wellname: [
            round(well._coordinates[i] + old_container._coordinates[i], 3)
            for i in [0, 1, 2]]
        for wellname, well in old_container.children_by_name.items()}

    new_wells = {
        wellname: [well._coordinates[i] for i in [0, 1, 2]]
        for wellname, well in new_container.children_by_name.items()}

    assert old_wells == new_wells


def test_one_serializer():
    plate = '6-well-plate'
    old_container = sqldb.load_container(plate)

    json_from_file = ldef._load_definition(test_defn_root, plate)
    json_from_container = ser.container_to_json(old_container)

    # Metadata comparison does not work in test, because the constructed
    # Container does not have a parent, and Container does not keep track of
    # its own name--the name is saved by the parent, so
    # new_json['metadata']['name'] in this test will be None

    assert json_from_container['ordering'] == json_from_file['ordering']
    assert json_from_container['wells'] == json_from_file['wells']
