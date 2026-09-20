from controller.spatial_annotations import visual_overlays


def test_locations_stay_with_their_source_image():
    images = [{'id': 'before'}, {'id': 'after'}]
    overlays = visual_overlays([
        {'image_id': 'after', 'label': 'Building', 'box': [.1, .2, .3, .4]},
        {'image_id': 'before', 'label': 'Ship', 'box': [0, 0, 1, 1]},
    ], images)
    assert [o['image_id'] for o in overlays] == ['before', 'after']
    assert overlays[0]['data'][0]['label'] == 'Ship'
    assert overlays[1]['data'][0]['box'] == [.1, .2, .3, .4]
    assert all(o['width'] == o['height'] == 1 for o in overlays)


def test_invalid_locations_never_become_boxes():
    base = {'image_id': 'img1', 'label': 'Building'}
    invalid = [None, [], [1, 0, 0, 1], [0, 0, 2, 1], [0, 0, float('nan'), 1],
               [False, 0, 1, 1], ['0', 0, 1, 1]]
    detections = [{**base, 'box': box} for box in invalid]
    detections += [{'image_id': 'unknown', 'label': 'Ship', 'box': [0, 0, 1, 1]},
                   {'image_id': [], 'label': 'Ship', 'box': [0, 0, 1, 1]}]
    assert visual_overlays(detections, [{'id': 'img1'}]) == []
    assert visual_overlays(None, [{'id': 'img1'}]) == []
