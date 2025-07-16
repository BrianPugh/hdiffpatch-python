The following files were generated with `hdiffz` v4.8.0

```bash
curl -O https://micropython.org/resources/firmware/RPI_PICO-20241129-v1.24.1.uf2
curl -O https://micropython.org/resources/firmware/RPI_PICO-20250415-v1.25.0.uf2

hdiffz RPI_PICO-20241129-v1.24.1.uf2 RPI_PICO-20250415-v1.25.0.uf2 RPI_PICO-20241129-v1.24.1-\>RPI_PICO-20250415-v1.25.0.hdiff
hdiffz -c-lzma -f RPI_PICO-20241129-v1.24.1.uf2 RPI_PICO-20250415-v1.25.0.uf2 RPI_PICO-20241129-v1.24.1-\>RPI_PICO-20250415-v1.25.0.hdiff.lzma
hdiffz -c-zlib -f RPI_PICO-20241129-v1.24.1.uf2 RPI_PICO-20250415-v1.25.0.uf2 RPI_PICO-20241129-v1.24.1-\>RPI_PICO-20250415-v1.25.0.hdiff.zlib
```
