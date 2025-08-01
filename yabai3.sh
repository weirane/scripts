#!/bin/zsh

BAR_HEIGHT=36

err() {
    echo "yabai3: $1"; exit 1
}

sidx() {
    yabai -m query --windows --window $@ | jq '."stack-index"'
}

resize() {
    (( $3 )) || err "resize: scale factor not a number: $3"

    case $1 in
        shrink) local r=$((-$3)) ;;
        grow) local r=$3 ;;
        *) err "resize: unknown scale: $1" ;;
    esac

    case $2 in
        width)
            yabai -m window --resize right:$r:0 2>/dev/null || yabai -m window --resize left:$r:0
            ;;
        height)
            yabai -m window --resize bottom:0:$r 2>/dev/null || yabai -m window --resize top:0:$r
            ;;
        *) err "resize: unknown orientation: $2" ;;
    esac
}

layout-toggle() {
    yabai -m space --layout $(yabai -m query --spaces --space | jq -r 'if .type == "bsp" then "stack" else "bsp" end')
}

toggle-dropdownterm() {
    if ! (tmux ls | grep -q 'dropdown:.*attached'); then
        $HOME/scripts/dropdownterm
        sleep 0.5
        local ddt_id=$(yabai -m query --windows | jq -r '.[] | select(."scratchpad" == "dropdownterm").id')
        [[ -n $ddt_id ]] && yabai -m window $ddt_id --toggle sticky
        return
    fi
    local ddt=$(yabai -m query --windows | jq -r '.[] | select(."scratchpad" == "dropdownterm")')
    if [[ -z $ddt ]]; then
        err "dropdownterm not found"
    fi
    local ddt_id=$(echo $ddt | jq -r '.id')
    local ddt_visible=$(echo $ddt | jq -r '."is-visible"')

    if [[ $ddt_visible == "true" ]]; then
        # make unsticky before hiding
        yabai -m window $ddt_id --toggle sticky
        yabai -m window $ddt_id --toggle dropdownterm
    else
        # make sticky and center after showing
        yabai -m window $ddt_id --toggle dropdownterm
        yabai -m window $ddt_id --toggle sticky
    fi
}

cmd=$1
shift
case $cmd in
    resize) resize $@ ;;
    layout-toggle) layout-toggle ;;
    toggle-dropdownterm) toggle-dropdownterm ;;
    *) err "unknown command: $cmd" ;;
esac
