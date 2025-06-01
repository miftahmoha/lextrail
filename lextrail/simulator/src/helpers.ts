import { VisNet, LTAction, LTNetwork } from './types';
import { DOM } from './interface'

export function getRequiredElement<T extends HTMLElement>(id: string): T {
    const element = document.getElementById(id) as T | null;
    if (!element) {
        throw new Error(`Required DOM element '${id}' not found`);;
    }
    return element;
}

export function updatePlayPauseButton(DOM: DOM, isPaused: boolean): void {
    const icon = DOM.buttons.btnPause.querySelector('i');
    if (!icon) {
        console.error("Pause/Resume icon not found.");
        return;
    }

    if (isPaused) {
        icon.className = 'fas fa-play';
    } else {
        icon.className = 'fas fa-pause';
    }
}

export function updateControlButtons(DOM: DOM, currentFrame: number, totalFrames: number,
    isPaused: boolean, isInterrupted: boolean, isComplete: boolean) {
    DOM.buttons.btnPause.disabled = isInterrupted || isComplete;
    updatePlayPauseButton(DOM, isPaused);
    DOM.buttons.btnPrev.disabled = currentFrame <= 1 || isInterrupted;
    DOM.buttons.btnNext.disabled = currentFrame >= totalFrames || isInterrupted;
    DOM.buttons.btnInterrupt.disabled = isInterrupted || isComplete;
    DOM.buttons.btnDelay.disabled = isInterrupted || isComplete;
    DOM.inputs.delayInput.disabled = isInterrupted || isComplete;
}

export function updateGraphFontColors(network: LTNetwork, root: HTMLElement): void {
    const color = root.classList.contains('light-mode') ? '#000000' : '#ffffff';

    // Update thumbnail graphs.
    network.sides.forEach((graph) => {
        if (graph) {
            const nodes = (graph as VisNet).body.data.nodes;
            nodes.forEach(node => {
                nodes.update({
                    id: node.id,
                    font: {
                        color: color
                    }
                });
            });
        }
    });

    // Update main graph.
    if (network.front) {
        const nodes = (network.front as VisNet).body.data.nodes;
        nodes.forEach(node => {
            nodes.update({
                id: node.id,
                font: {
                    color: color
                }
            });
        });
    }
}


// Sending data to the server.
export function sendControlCommand(action: LTAction, extraData: { rate?: number } = {}) {
    const data = {
        action: action,
        ...extraData
    };
    fetch('/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
        .then(response => response.json())
        .then(data => {
            console.log('Control command response:', data);
        })
        .catch(error => {
            console.error('Error sending control command:', error);
        });
}