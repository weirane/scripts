#!/bin/sh

set -e

if [ ! -f "$1" ]; then
    echo >&2 "'$1' is not a valid file"
    exit 1
fi

case $1 in
    *.pkg.tar.zst)
        dir=${1%.pkg.tar.zst}
        mkdir "$dir" || exit 1
        tar -C "$dir" --zstd -xf "$1"
        ;;
    *.pkg.tar.xz)
        dir=${1%.pkg.tar.xz}
        mkdir "$dir" || exit 1
        tar -C "$dir" -xJf "$1"
        ;;
    *.deb)
        dir="${1%.deb}"
        mkdir "$dir" || exit 1
        ar x --output "$dir" "$1"
        ;;
    *.tar.bz2) tar xjf "$1"   ;;
    *.tar.gz)  tar xzf "$1"   ;;
    *.tar.xz)  tar xJf "$1"   ;;
    *.lzma)    unlzma "$1"    ;;
    *.bz2)     bunzip2 "$1"   ;;
    *.rar)     unrar x "$1"   ;;
    *.gz)      gunzip "$1"    ;;
    *.tar)     tar xf "$1"    ;;
    *.tbz2)    tar xjf "$1"   ;;
    *.tgz)     tar xzf "$1"   ;;
    *.zip)     unzip "$1"     ;;
    *.Z)       uncompress "$1";;
    *.7z)      7z x "$1"      ;;
    *)         echo >&2 "'$1' cannot be extracted via ex";;
esac
