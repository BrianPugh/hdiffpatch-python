The following files were generated with `hdiffz` v5.0.1

```bash
curl -O https://micropython.org/resources/firmware/RPI_PICO-20241129-v1.24.1.uf2
curl -O https://micropython.org/resources/firmware/RPI_PICO-20250415-v1.25.0.uf2

hdiffz RPI_PICO-20241129-v1.24.1.uf2 RPI_PICO-20250415-v1.25.0.uf2 RPI_PICO-20241129-v1.24.1-\>RPI_PICO-20250415-v1.25.0.hdiff
hdiffz -c-lzma -f RPI_PICO-20241129-v1.24.1.uf2 RPI_PICO-20250415-v1.25.0.uf2 RPI_PICO-20241129-v1.24.1-\>RPI_PICO-20250415-v1.25.0.hdiff.lzma
hdiffz -c-zlib -f RPI_PICO-20241129-v1.24.1.uf2 RPI_PICO-20250415-v1.25.0.uf2 RPI_PICO-20241129-v1.24.1-\>RPI_PICO-20250415-v1.25.0.hdiff.zlib
```

The `.hdiff.tamp` (extended v2 format) and `.hdiff.tamp-v1` (`TampConfig(extended=False)`, tamp v1.x-compatible format) files were generated with hdiffpatch-python v2.0.0 (tamp v2.3.0). They are pinned so future releases keep decoding diffs produced by older releases in both formats.
