// Globals.
let allPreviousData = [];
let allThumbnailGraphs = [];
let allSidebarItems = [];
let mainNetwork = null;
let shouldFetch = true;
let isPaused = false;
let isInterrupted = false;
let isComplete = false;
let totalFrames = 0;
let currentFrame = 0;


// Control elements.
const btnPrev = document.getElementById('btn-prev');
const btnTogglePause = document.getElementById('btn-toggle-pause');
const btnNext = document.getElementById('btn-next');
const btnInterrupt = document.getElementById('btn-interrupt');
const btnReset = document.getElementById('btn-reset');
const speedInput = document.getElementById('speed-input');
const applySpeedBtn = document.getElementById('apply-speed');


// Event handlers for controls.
btnTogglePause.addEventListener('click', () => {
    sendControlCommand('toggle_pause');
});
btnPrev.addEventListener('click', () => {
    updateGraphs(allPreviousData.rollbacks[currentFrame - 1]);
    currentFrame -= 1;
    updateFrameCounter(currentFrame, totalFrames);
});
btnNext.addEventListener('click', () => {
    updateGraphs(allPreviousData.updates[currentFrame]);
    currentFrame += 1;
    updateFrameCounter(currentFrame, totalFrames);
});
btnInterrupt.addEventListener('click', () => {
    if (confirm('Are you sure you want to interrupt the simulation? This cannot be undone.')) {
        sendControlCommand('interrupt');
    }
});
btnReset.addEventListener('click', () => {
    if (confirm('Are you sure you want to reset the simulation?')) {
        currentFrame = 0;
        shouldFetch = true;
        document.querySelectorAll('.sidebar-item').forEach(el => {
            el.remove();
        });
        sendControlCommand('reset');
    }
});
applySpeedBtn.addEventListener('click', () => {
    const value = parseInt(speedInput.value);
    if (!isNaN(value) && value >= 0) {
        sendControlCommand('set_speed', { rate: value / 1000 });
    }
});

// Sending data to the server.
function sendControlCommand(action, extraData = {}) {
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


function updateFrameCounter(current, total) {
    document.getElementById('frame-counter').textContent = `Frame ${current}/${total}`;
}


function updateControlButtons() {
    btnTogglePause.disabled = isInterrupted || isComplete;
    btnTogglePause.textContent = isPaused ? "Resume" : "Pause";
    btnPrev.disabled = currentFrame <= 1 || isInterrupted;
    btnNext.disabled = currentFrame >= totalFrames || isInterrupted;
    btnInterrupt.disabled = isInterrupted || isComplete;
    speedInput.disabled = isInterrupted || isComplete;
    applySpeedBtn.disabled = isInterrupted || isComplete;

    if (isInterrupted) {
        btnInterrupt.textContent = "Interrupted";
    }
}


// Transition animations.
// Convert HEX to RGB object.
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
}

// Color interpolation.
function interpolateColor(fromColor, toColor, progress) {
    const from = hexToRgb(fromColor);
    const to = hexToRgb(toColor);

    const r = Math.round(from.r + (to.r - from.r) * progress);
    const g = Math.round(from.g + (to.g - from.g) * progress);
    const b = Math.round(from.b + (to.b - from.b) * progress);

    return `rgb(${r}, ${g}, ${b})`;
}

// Highlight animation function.
function animateHighlightTransitionWithAnimation(
    network,
    fromId,
    toId,
    highlightColor = '#f1c232',
    dimColor = "#f3f6f4",
    duration = 1000
) {
    const startTime = performance.now();

    const nodes = network.body.data.nodes;
    const fromNode = fromId ? nodes.get(fromId) : null;
    const toNode = toId ? nodes.get(toId) : null;

    if (!toNode) {
        throw new Error("Highlight sent to an invalid node.");
    }

    const originalNewColor = toNode.color?.background || '#97C2FC';
    const originalOldColor = fromNode?.color?.background || '#97C2FC';

    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Update new node.
        nodes.update({
            id: toId,
            color: {
                background: interpolateColor(originalNewColor, highlightColor, progress),
                border: interpolateColor(originalNewColor, highlightColor, progress)
            }
        });

        // Update old node if it exists.
        if (fromNode) {
            nodes.update({
                id: fromId,
                color: {
                    background: interpolateColor(originalOldColor, dimColor, progress),
                    border: interpolateColor(originalOldColor, dimColor, progress)
                }
            });
        }

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    requestAnimationFrame(animate);
}

// Temporary classic transition.
function animateHighlightTransition(network, fromId, toId) {
    const nodes = network.body.data.nodes;
    const fromNode = fromId ? nodes.get(fromId) : null;
    const toNode = toId ? nodes.get(toId) : null;

    if (!toNode) {
        throw new Error("Highlight sent to an invalid node.");
    }

    // Update toNode to orange.
    nodes.update({
        id: toId,
        color: {
            background: 'orange',
            border: 'orange'
        }
    });

    // Update fromNode to lightblue (if it exists).
    if (fromNode) {
        nodes.update({
            id: fromId,
            color: {
                background: 'lightblue',
                border: 'lightblue'
            }
        });
    }
}


// Graph updates.
function updateGraphs(currentUpdates) {
    let sidebarItems = document.getElementById('sidebar-items');

    // Deletion.
    // First, collect all indices that need to be deleted.
    const indicesToDelete = Object.keys(currentUpdates.delu).map(Number).sort((a, b) => b - a);

    // Then delete from highest to lowest to avoid index shifting problems.
    indicesToDelete.forEach(index => {
        const sidebarItem = document.getElementById(`sidebar-item-${index}`);
        if (sidebarItem) {
            sidebarItems.removeChild(sidebarItem);
            if (allThumbnailGraphs[index]) {
                allThumbnailGraphs[index].destroy();
                allThumbnailGraphs.splice(index, 1);
            }
        } else {
            console.warn(`Sidebar item with ID sidebar-item-${index} was not found for deletion.`);
        }
    });

    // Addition.
    // Add graphs.
    Object.keys(currentUpdates.addu).forEach(index => {
        // Creating the thumbnail.
        const item = document.createElement('div');
        item.className = 'sidebar-item';
        item.id = `sidebar-item-${index}`;
        // The `${index + 1}` could take `n, m` indices from the backend.
        item.innerHTML = `
            <div>Subgraph ${index}</div>
            <div class="sidebar-thumbnail" id="thumbnail-${index}"></div>
        `;
        // Click event.
        item.onclick = function () {
            document.querySelectorAll('.sidebar-item').forEach(el => {
                el.classList.remove('active');
            });
            this.classList.add('active');
            displayGraph(index);
        };
        sidebarItems.appendChild(item);
        // Plot and store graph at index.
        const container = document.getElementById(`thumbnail-${index}`);
        const options = {
            nodes: { shape: "dot", size: 20 },
            edges: { arrows: "to" },
        };
        const graphDataClone = structuredClone(currentUpdates.addu[index]);
        allThumbnailGraphs[index] = new vis.Network(container, graphDataClone, options);
    });

    // Set the sidebar item with highest index as active.
    const index = allThumbnailGraphs.length - 1
    if (index >= 0) {
        const activeItem = document.getElementById(`sidebar-item-${index}`);
        if (activeItem) {
            // Add active class.
            activeItem.classList.add('active');
            // Optionally display this graph by default.
            displayGraph(index);
        }
    }

    // Move.
    // Moving the highlight to the next node.
    Object.keys(currentUpdates.movu).forEach(index => {
        const indices = currentUpdates.movu[index];
        if (indices) {
            for (const [fromId, toId] of Object.entries(indices)) {
                // To reverse back to a previous state, we need to keep a {lastVisitedID: ""} after each `deletion`,
                // which breaks the code because the first operation we do after recieving 
                // a vizUpdate instance is `deletion`, thus we move nodes of a deleted graph.
                // (deletion has to be before addition and `moving` has to be before `addition`).
                if (!toId) continue;
                animateHighlightTransition(allThumbnailGraphs[index], fromId, toId);
            }
        }
        else {
            console.warn(`No valid transition indices.`);
        }
    });
}


// Displays graphs from the sidebar.
function displayGraph(index) {
    const container = document.getElementById('current-graph');
    const options = {
        nodes: { shape: "dot", size: 20 },
        edges: { arrows: "to" },
    };
    // Get the network instance at index.
    const networkInstance = allThumbnailGraphs[index];
    // Get its nodes and edges then build a clone.
    // [TODO] For it to be the same graph displayed in both the sidebar and at the center is much better.
    const graphDataClone = {
        nodes: networkInstance.nodesHandler.body.data.nodes,
        edges: networkInstance.edgesHandler.body.data.edges,
    };
    if (mainNetwork) {
        mainNetwork.setData(graphDataClone);
    } else {
        mainNetwork = new vis.Network(container, graphDataClone, options);
    }
    document.getElementById('status').innerHTML = `Displaying Subgraph ${+index + 1} of ${allThumbnailGraphs.length}`;
}


function loadGraphs() {
    if (!shouldFetch) null;

    fetch("/graph")
        .then(response => response.json())
        .then(data => {
            if (JSON.stringify(data.updates) !== JSON.stringify(allPreviousData.updates)) {

                allPreviousData = data;

                const newUpdates = data.updates.slice(currentFrame);
                newUpdates.forEach(update => {
                    updateGraphs(update)
                });

                totalFrames = data.updates.length
                // A copy to act upon when transitioning between frames.
                currentFrame = data.updates.length;

                // Update frames.
                updateFrameCounter(currentFrame, totalFrames);
            }

            // Update LLM response (fragmented strings allows simple transitions to previous frames).
            document.getElementById('llm-response').value = data._response.slice(0, currentFrame).join('') || "No response available";

            // Update simulation state
            isPaused = data._is_paused;
            isInterrupted = data._is_interrupted;
            isComplete = data._is_simulation_complete;

            // Update control buttons
            updateControlButtons();

            // Check if simulation is complete
            if (isComplete || isInterrupted) {
                shouldFetch = false
                if (isInterrupted) {
                    document.getElementById('status').innerHTML =
                        `Simulation interrupted. Displaying Subgraph ${allThumbnailGraphs.length} of ${allThumbnailGraphs.length}`;
                } else if (isComplete) {
                    document.getElementById('status').innerHTML =
                        `Simulation complete. Displaying Subgraph ${allThumbnailGraphs.length} of ${allThumbnailGraphs.length}`;
                }
            }

            loadGraphs();

        })
        .catch(error => {
            console.error("Error loading graphs:", error);
            document.getElementById('status').innerHTML = "Failed to load graphs. Check server connection.";
        });
}

loadGraphs();
