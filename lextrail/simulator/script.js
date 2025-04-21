// Globals.
let allPreviousData = [];
let allThumbnailGraphs = [];
let allSidebarItems = [];
let lastActiveItem = null;
let mainNetwork = null;
let shouldFetch = true;
let isPaused = false;
let isInterrupted = false;
let isComplete = false;
let totalFrames = 0;
let currentFrame = 0;


// Theme modes.
const themeToggle = document.getElementById('theme-toggle');
const root = document.documentElement;
const icon = themeToggle.querySelector('i');

// Font color update for each mode.
function updateGraphFontColors() {
    const newFontColor = root.classList.contains('light-mode')? '#000000' : '#ffffff';

    // Update thumbnail graphs.
    allThumbnailGraphs.forEach((graph, index) => {
        if (graph) {
            const nodes = graph.body.data.nodes;
            nodes.forEach(node => {
                nodes.update({
                    id: node.id,
                    font: {
                        color: newFontColor
                    }
                });
            });
        }
    });

    // Update display graph.
    if (mainNetwork) {
        const nodes = mainNetwork.body.data.nodes;
        nodes.forEach(node => {
            nodes.update({
                id: node.id,
                font: {
                    color: newFontColor
                }
            });
        });
    }
}

// Mode transitions. 
themeToggle.addEventListener('click', () => {
    if (root.classList.contains('light-mode')) {
        root.classList.remove('light-mode');
        icon.className = 'fas fa-sun';
        localStorage.setItem('theme', 'dark');
    } else {
        root.classList.add('light-mode');
        icon.className = 'fas fa-moon';
        localStorage.setItem('theme', 'light');
    }
    updateGraphFontColors()
});


// Control elements.
const btnPrev = document.getElementById('btn-prev');
const btnTogglePause = document.getElementById('btn-toggle-pause');
const btnNext = document.getElementById('btn-next');
const btnInterrupt = document.getElementById('btn-interrupt');
const btnReset = document.getElementById('btn-reset');
const speedInput = document.getElementById('speed-input');
const speedSlider = document.getElementById('speed-slider');
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
speedSlider.addEventListener('input', () => {
    speedInput.value = speedSlider.value;
});

speedInput.addEventListener('input', () => {
    speedSlider.value = speedInput.value;
});
applySpeedBtn.addEventListener('click', () => {
    const value = parseInt(speedInput.value);
    if (!isNaN(value) && value >= 0) {
        sendControlCommand('set_speed', { rate: value / 1000 });
    }
});

// Update play/pause button icon.
function updatePlayPauseButton() {
    const icon = btnTogglePause.querySelector('i');
    if (isPaused) {
        icon.className = 'fas fa-play';
    } else {
        icon.className = 'fas fa-pause';
    }
}

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
    updatePlayPauseButton();
    btnPrev.disabled = currentFrame <= 1 || isInterrupted;
    btnNext.disabled = currentFrame >= totalFrames || isInterrupted;
    btnInterrupt.disabled = isInterrupted || isComplete;
    speedInput.disabled = isInterrupted || isComplete;
    applySpeedBtn.disabled = isInterrupted || isComplete;
}

// Moves the highlight from a node A to a node B.
function moveHighlight(network, fromId, toId) {
    const nodes = network.body.data.nodes;
    const fromNode = fromId ? nodes.get(fromId) : null;
    const toNode = toId ? nodes.get(toId) : null;

    if (!toNode) {
        throw new Error("Highlight sent to an invalid node.");
    }

    // Update toNode to highlighted state.
    nodes.update({
        id: toId,
        color: {
            background: '#06b6d4',
            border: '#06b6d4'
        },
        shadow: {
            enabled: true,
            color: '#06b6d4',
            size: 10,
            x: 0,
            y: 0
        },
    });

    // Reset fromNode to default color if it exists.
    if (fromNode) {
        nodes.update({
            id: fromId,
            color: {
                background: 'lightblue',
                border: 'rgba(255, 255, 255, 0.05)',
            },
            shadow: {
                enabled: false,
            },
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
        sidebarItem.classList.add('sidebar-item-remove');
        if (sidebarItem) {
            // sidebarItems.removeChild(sidebarItem);
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
        // Check if there's an existing item with this index.
        const existingItem = document.getElementById(`sidebar-item-${index}`);

        if (existingItem) {
            // If it exists, remove the `fadeSlideOut` animation and add the `fadeSlideIn` one.
            existingItem.classList.remove('sidebar-item-remove');
            existingItem.classList.add('sidebar-item-new');
            // Plot and store graph at index.
            const container = document.getElementById(`thumbnail-${index}`);
            const options = {
                nodes: {
                    shape: "dot",
                    size: 15,
                    color: {
                        background: 'rgba(173, 216, 230, 1)',
                        border: 'rgba(255, 255, 255, 0.5)',
                    },
                    font: {
                        face: 'Space Mono',
                        color: root.classList.contains('light-mode')? '#000000' : '#ffffff',
                        size: 0,
                        strokeWidth: 0
                    },
                },
                edges: {
                    arrows: "to",
                    color: {
                        color: 'rgba(255, 255, 255, 0.2)',
                        highlight: '#06b6d4'
                    },
                    width: 1
                },
            };
            const graphDataClone = structuredClone(currentUpdates.addu[index]);
            allThumbnailGraphs[index] = new vis.Network(container, graphDataClone, options);
        } else {
            // Creating the thumbnail.
            const item = document.createElement('div');
            item.className = 'sidebar-item';
            item.id = `sidebar-item-${index}`;
            // Add the `fadeSlideIn` animation.
            item.classList.add('sidebar-item-new');
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
                nodes: {
                    shape: "dot",
                    size: 15,
                    color: {
                        background: 'rgba(173, 216, 230, 1)',
                        border: 'rgba(255, 255, 255, 0.5)',
                    },
                    font: {
                        face: 'Space Mono',
                        color: root.classList.contains('light-mode')? '#000000' : '#ffffff',
                        size: 0,
                        strokeWidth: 0
                    },
                },
                edges: {
                    arrows: "to",
                    color: {
                        color: 'rgba(255, 255, 255, 0.2)',
                        highlight: '#06b6d4'
                    },
                    width: 1
                },
            };
            const graphDataClone = structuredClone(currentUpdates.addu[index]);
            allThumbnailGraphs[index] = new vis.Network(container, graphDataClone, options);
        }
    });


    // Set the sidebar item with highest index as active.
    const index = allThumbnailGraphs.length - 1;
    if (index >= 0) {
        activeItem = document.getElementById(`sidebar-item-${index}`);
        if (activeItem && lastActiveItem !== activeItem) {
            // Disable the last activated sidebar item if different.
            if (lastActiveItem) {
                lastActiveItem.classList.remove('active');
            }
            // Add active class.
            activeItem.classList.add('active');
            // Display its graph on the main block by default.
            displayGraph(index);
            // Save it.
            lastActiveItem = activeItem
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
                moveHighlight(allThumbnailGraphs[index], fromId, toId);
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
    // Add fade class
    container.classList.add('graph-fade');

    // Remove the class after animation completes
    setTimeout(() => {
        container.classList.remove('graph-fade');
    }, 500);

    const options = {
        nodes: {
            shape: "dot",
            size: 20,
            color: {
                background: 'rgba(173, 216, 230, 1)',
                border: 'rgba(255, 255, 255, 0.5)',
            },
            font: {
                face: 'Space Mono',
                color: root.classList.contains('light-mode')? '#000000' : '#ffffff',
                size: 14,
                strokeWidth: 0
            },
        },
        edges: {
            arrows: "to",
            color: {
                color: 'rgba(255, 255, 255, 0.2)',
                highlight: '#06b6d4'
            },
            width: 1.5
        },
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
        // If the theme changes.
        mainNetwork.setOptions(options);
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
