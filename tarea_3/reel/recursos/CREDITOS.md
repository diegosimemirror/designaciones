# Créditos y licencias del reel

| Recurso | Autor / fuente | Licencia |
|---|---|---|
| Narración | Voz propia del autor, grabada y editada (sin clonación ni voz sintética) | — |
| Música: «Clean Soul» (extracto en `musica_clean_soul_extracto.mp3`) | Kevin MacLeod (incompetech.com) | Creative Commons Atribución 4.0 — https://creativecommons.org/licenses/by/4.0/ |
| Datos | Diario Oficial El Peruano: normas de designación, conclusión y renuncia, nov-2022 a oct-2026 | Información pública oficial |
| Gráficos animados, red, mapa de días y créditos | Elaboración propia con los datos (Python: Pillow, pandas) | Igual que el repositorio |
| Captura del dashboard (`dashboard_movil.png`) | Elaboración propia | Igual que el repositorio |

Atribución de la música, en el formato que pide el autor:
"Clean Soul" Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/

## Cómo se hizo el reel (reproducible)

1. `reel/01_transcribir.py`: transcribe la narración con Whisper large-v3-turbo (faster-whisper, licencia MIT), con tiempos por palabra.
2. `reel/02_editar_audio.py`: solo recorta frases completas entre pausas naturales (criterio acordado con el autor), acorta las
   pausas largas a 0,4 s, acelera un 8 % sin cambiar el tono (ffmpeg `atempo`) y nivela el volumen a -16 LUFS. Las ideas
   de las frases recortadas pasan a la pantalla como texto. Versión entregada: "corta" (79 s).
3. `reel/03_hacer_video.py`: dibuja cada cuadro con los datos (sin nombres), sincroniza las escenas con la narración, agrega
   subtítulos (`subtitulos.srt`) y mezcla la música 17 dB por debajo de la voz.

Entorno: Python 3.12 aparte del de Anaconda (`uv venv`; paquetes `faster-whisper imageio-ffmpeg pillow numpy pandas soundfile`).
La grabación cruda de la voz (`reel/voz/`) no se publica.
