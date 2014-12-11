#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import geobuf_pb2
import collections


def add_point(line_string, point):
    for x in point: line_string.coords.append(int(x * 1e6))

def populate_linestring(line_string, seq):
    prevPoint = None
    for point in seq:
        if prevPoint is None: add_point(line_string, point)
        else: add_point(line_string, [a - b for a, b in zip(point, prevPoint)]) # delta encoding
        prevPoint = point

def encode_geometry(geometry, geometry_json):

    gt = geometry_json['type']

    Geometry = geobuf_pb2.Data.Geometry
    geometry.type = {
        'Point': Geometry.POINT,
        'MultiPoint': Geometry.MULTIPOINT,
        'LineString': Geometry.LINESTRING,
        'MultiLineString': Geometry.MULTILINESTRING,
        'Polygon': Geometry.POLYGON,
        'MultiPolygon': Geometry.MULTIPOLYGON
    }[gt]

    coords_json = geometry_json.get('coordinates')

    if gt == 'Point':
        add_point(geometry.line_string, coords_json)

    elif gt in ('MultiPoint', 'LineString'):
        populate_linestring(geometry.line_string, coords_json)

    elif gt in ('MultiLineString','Polygon'):
        line_strings = geometry.multi_line_string.line_strings
        for seq in coords_json: populate_linestring(line_strings.add(), seq)

    elif gt in ('MultiPolygon'):
        for polygons in coords_json:
            poly = geometry.multi_polygon.polygons.add()
            for seq in polygons: populate_linestring(poly.line_strings.add(), seq)


def encode_feature(data, feature, feature_json):

    if 'id' in feature_json:
        id = feature_json['id']
        if isinstance(id, int) and id >= 0: feature.uint_id = idts
        else: feature.id = id

    geometry_json = feature_json.get('geometry')

    if geometry_json['type'] == 'GeometryCollection':
        for single_geometry_json in geometry_json.get('geometries'):
            encode_geometry(feature.geometry_collection.geometries.add(), single_geometry_json)
    else:
        encode_geometry(feature.geometry, geometry_json)


    keys = collections.OrderedDict()
    valueIndex = 0

    for key, val in feature_json.get('properties').viewitems():
        if not (key in keys):
            keys[key] = True
            data.keys.append(key)

        feature.properties.append(keys.keys().index(key))
        feature.properties.append(valueIndex)

        valueIndex += 1

        value = data.values.add()

        if isinstance(val, unicode):
            value.string_value = val

        elif isinstance(val, float):
            value.double_value = val

        elif isinstance(val, int) or isinstance(val, long):
            value.int_value = val

        elif isinstance(val, bool):
            value.bool_value = val


def encode(obj):

    data = geobuf_pb2.Data()
    data_type = obj['type']

    if data_type == 'FeatureCollection':
        for feature_json in obj.get('features'):
            encode_feature(data, data.feature_collection.features.add(), feature_json)

    elif data_type == 'Feature':
        encode_feature(data, data.feature, obj)

    elif data_type == 'GeometryCollection':
        for geometry_json in obj.get('geometries'):
            encode_geometry(data.geometry_collection.geometries.add(), geometry_json)
    else:
        encode_geometry(data.geometry, obj)

    return data.SerializeToString();


if __name__ == '__main__':
    filename = sys.argv[1]
    data = open(filename,'rb').read()
    json_object = json.loads(data)

    proto = encode(json_object)

    print '%d bytes' % (len(proto))
    open(filename + '.pbf', 'wb').write(proto)