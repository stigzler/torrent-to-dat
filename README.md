# torrent-to-dat
Converts torrent files to logiqx .dat files

## Example

Example use case: There is no redump .dat file for WiiU. There is a .torrent file for WiiU. You feed the .torrent file into this app which produces a .dat file in the same format as redump dats (logiqx). You can then feed this into Retool to produce a 1G1R .dat.

## How to Use

Requires **Python 3** (no external dependencies).

```bash
python torrent-to-dat.py <input.torrent> [output.dat]
```

### Parameters

| Parameter | Required | Description |
| :--- | :---: | :--- |
| `input.torrent` | Yes | Path to the source `.torrent` file. |
| `output.dat` | No | Custom path/filename for the generated DAT. Defaults to `<input>.dat`. |

### Examples

**Default output filename** (generates `MySet.dat`):
```bash
python torrent-to-dat.py "MySet.torrent"
```

**Custom output filename:**
```bash
python torrent-to-dat.py "Minerva_Myrient - Redump - Nintendo - Wii U - WUX.torrent" "Nintendo - WiiU - Datfile (From Minerva Torrent) (2026-11-20).dat"
```


