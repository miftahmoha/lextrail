import { Py_Recieve, Ts_State } from './types';
import { updateControlButtons } from './helpers';
import { updateFrame, updateGraphs } from './render';
import { DOM, addEventListeners } from './interface';

async function loadGraphs(state: Ts_State): Promise<void> {
    const DEFAULT_POLL_DELAY = 1000;

    while (state.fetch) {
        try {
            const response = await fetch("/graph");
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

            const content: Py_Recieve = await response.json();

            const prevData = state.response.data;
            const recvData = content.data;

            if (JSON.stringify(recvData) !== JSON.stringify(prevData) || !prevData.completed) {
                await updateFrame(DOM, state, recvData);
            }

            const isPaused = content.setting.paused;
            const isInterrupted = content.setting.interrupted;
            const isComplete = content.data.completed;

            const totalFrames = recvData.results.length;

            if (isComplete) {
                DOM.display.status.innerHTML =
                    `Simulation complete. Displaying frame ${totalFrames} of ${totalFrames}`;
            }
            else
                DOM.display.status.innerHTML = "Loading graphs from server...";

            updateControlButtons(DOM, state.frame, totalFrames,
                isPaused, isInterrupted, isComplete);

            DOM.display.frameCounter.textContent = `Frame ${state.frame}/${totalFrames}`;

            // Fragmented strings allow simple transitions to previous frames.
            DOM.display.llmResponse.value = state.response.data.response.slice(0, state.frame).join('') || "No response available";

            if (isInterrupted) {
                DOM.display.status.innerHTML =
                    `Simulation interrupted. Displaying frame ${totalFrames} of ${totalFrames}`;

                state.fetch = false;
            }
        }
        catch (error) {
            console.error("Error loading graphs:", error);
            document.getElementById('status')!.innerHTML = "Failed to load graphs. Check server connection.";
        }

        await new Promise(resolve => setTimeout(resolve, DEFAULT_POLL_DELAY));
    }
}

async function main() {
    const INITIAL_STATE: Ts_State = {
        response: {
            data: {
                "results": [],
                "response": [],
                "completed": false,
            },
            setting: {
                "paused": false,
                "interrupted": false,
                "reset": false,
            }
        }, interfaces: [], networks: [], frame: 0, active: [], fetch: true
    };

    INITIAL_STATE.active.push([])

    addEventListeners(DOM, INITIAL_STATE, updateGraphs);

    loadGraphs(INITIAL_STATE);
}

main();