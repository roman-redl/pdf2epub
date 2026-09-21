#!/bin/zsh
# run_chunks.zsh IN_FOLDER OUTROOT DPI TOTAL_PAGES [CHUNK]
# Чанковый прогон marker 2.0: таймаут-смерть -> половинение чанка -> продолжение.
cd ~/personal-projects/pdf2epub
IN=$1; OUTROOT=$2; DPI=$3; TOTAL=$4; CHUNK=${5:-24}
mkdir -p $OUTROOT
p=0
while (( p < TOTAL )); do
  q=$(( p + CHUNK - 1 )); (( q > TOTAL - 1 )) && q=$(( TOTAL - 1 ))
  seg="$OUTROOT/seg_$(printf %04d $p)_$(printf %04d $q)"
  log="$seg.log"
  if [[ -f $seg/.done ]]; then p=$(( q + 1 )); continue; fi
  echo "[$(date +%H:%M:%S)] чанк $p-$q (размер $CHUNK)"
  TMO=$(( 240 + (q - p + 1) * 25 ))   # таймаут: 4 мин + 25с/страница
  .venv/bin/marker "$IN" --page_range $p-$q --force_ocr --highres_image_dpi $DPI --output_format markdown --output_dir "$seg" > $log 2>&1 &
  MPID=$!
  ( sleep $TMO; pkill -9 -f "output_dir $seg" 2>/dev/null; kill -9 $MPID 2>/dev/null ) & WPID=$!
  wait $MPID; rc=$?
  kill $WPID 2>/dev/null; wait $WPID 2>/dev/null
  if [[ $rc -eq 0 ]] && [[ -n $(find $seg -name "*.md" 2>/dev/null) ]]; then
    touch $seg/.done; echo "[$(date +%H:%M:%S)] ок"
    p=$(( q + 1 ))
  else
    echo "[$(date +%H:%M:%S)] чанк $p-$q ПАЛ (rc=$rc), чистка и половинение"
    pkill -9 -f "surya\." 2>/dev/null; pkill -9 -f llama-server 2>/dev/null; sleep 3
    CHUNK=$(( CHUNK / 2 )); (( CHUNK < 4 )) && CHUNK=4
  fi
done
echo "ALL_CHUNKS_DONE $OUTROOT"
