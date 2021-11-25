# P2P Protocol Design

There are some types of protocol we need to design:

1. Peer to Peer

2. Peer to Tracker

3. Metadata and torrent file format, including how to partition files and folder

### How to download

1. The peer asks trackers for all peers that hold the target torrent.

2. The peer communicates with all peers and download the metadata, i.e., the torrent file.

3. The peer communicates with all peers and download files in the torrent.

### Torrent file

A torrent file is a json file that describes folder structures, file name, file hash and hash of every partition.

The Torrent Metadata is the field `torrent_hash`.

```json
{
  "name": "The name of this torrent",
  "torrent_hash": "The hash of current json object, with this field empty",
  "block_size" : "integer, indicates the block size",
  "files": [
    // A json array of file object, order guaranteed but not important
    {
      // A file object
      "name": "The name of this file",
      "dir": "relative path to this torrent, can be empty",
      "size": "integer, The size of file in bytes, must be 0 for a folder",
      "hash": "For a file: SHA256 of the whole file; For a folder: empty string",
      "blocks": [
        // Every blocks excluiding the last one must have the same size
        {
          // A block object
          "seq": "integer, globally sequence number",
          "size": "integer, size of current partition in bytes, should be 4096",
          "hash": "SHA256 of this file partition"
        }
      ]
    }
  ]
}
```

Here we define two functions:

1. `hash_json_object`

2. `hash_json_array`

They must be platform-indepentent and generate the same result for two EQUAL json objects/arrays.

We define two json objects/arrays are EQUAL iff:

1. They have the same key-value pairs

2. Order matters for array

3. Order does not matter for object (they are unordered set)

4. space and tabs that are not in keys or values do not matter

https://json-ld.org/ may help.

### Communication Protocol

