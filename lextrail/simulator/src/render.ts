import { VisNet, LTId, LTEdge, LTGraph, LTUpdate, LTData, LTNetwork, LTState, Network } from './types'
import { getRequiredElement } from './helpers';
import { DOM } from './interface'
import { Options } from "vis";

const VIS_MAIN_OPTIONS: Options = {
    nodes: {
        shape: "dot",
        size: 20,
        color: {
            background: 'rgba(173, 216, 230, 1)',
            border: 'rgba(255, 255, 255, 0.5)',
        },
        font: {
            face: 'Space Mono',
            color: DOM.root.classList.contains('light-mode') ? '#000000' : '#ffffff',
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
    physics: {
        enabled: true,
        solver: "forceAtlas2Based",
        stabilization: {
            enabled: true,
            iterations: 1000,
            updateInterval: 25,
        },
    },
};


const VIS_SIDE_OPTIONS: Options = {
    nodes: {
        shape: "dot",
        size: 15,
        color: {
            background: 'rgba(173, 216, 230, 1)',
            border: 'rgba(255, 255, 255, 0.5)',
        },
        font: {
            face: 'Space Mono',
            color: DOM.root.classList.contains('light-mode') ? '#000000' : '#ffffff',
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

// Displays graphs from the sidebar to the main block.
function displayGraph(network: LTNetwork, index: number, delay: number) {
    const container = getRequiredElement<HTMLElement>('current-graph')

    // Add fade class.
    container.classList.add('graph-fade');

    // Remove the class after animation completes, if it stays, the animation will not
    // happen since we're we'll be adding an existant animation class in the next frame.
    setTimeout(() => {
        container.classList.remove('graph-fade');
    }, delay / 2);

    // Get the network instance at index.
    const networkInstance = network.sides[index];

    // Get its nodes and edges then build a clone.
    // [TODO] Use a reference and not a copy. 
    const graphDataClone = {
        nodes: (networkInstance as VisNet).body.data.nodes,
        edges: (networkInstance as VisNet).body.data.edges,
    } as any;

    // let networkFront = network.front;

    if (network.front) {
        network.front.setData(graphDataClone);
        network.front.setOptions({
            nodes: {
                font: {
                    color: DOM.root.classList.contains('light-mode') ? '#000000' : '#ffffff'
                }
            }
        });
    } else {
        network.front = new Network(container, graphDataClone, VIS_MAIN_OPTIONS);
    }

    const status = getRequiredElement('status');
    status.innerHTML = `Displaying Subgraph ${+index + 1} of ${network.sides.length}`;
}

// Moves the highlight from a node A to a node B.
function moveHighlight(network: Network, fromId: string, toId: string): void {
    const nodes = (network as VisNet).body.data.nodes;
    const fromNode = fromId ? nodes.get(fromId) : null;
    const toNode = toId ? nodes.get(toId) : null;

    if (!toNode) {
        throw new Error("Highlight sent to an invalid node.");
    }

    // Update `toNode` to highlighted state.
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

    // Reset `fromNode` to default color if it exists.
    if (fromId !== toId && fromNode) {
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


function handleDeletions(deletions: Record<number, LTGraph>, thumbnailGraphs: Network[]) {
    // First, collect all indices that need to be deleted.
    const indicesToDelete: number[] = Object.keys(deletions).map(Number).sort((a, b) => b - a);

    // Then delete from highest to lowest to avoid index shifting problems.
    indicesToDelete.forEach(index => {
        const sidebarItem = getRequiredElement<HTMLElement>(`sidebar-item-${index}`);

        // A simple slide animation.
        sidebarItem.classList.add('sidebar-item-remove');

        if (thumbnailGraphs[index]) {
            thumbnailGraphs[index].destroy();
            thumbnailGraphs.splice(index, 1);
        }
    });
}


function handleAdditions(additions: Record<number, LTGraph>, network: LTNetwork, delay: number) {
    const sidebarItems = getRequiredElement<HTMLElement>('sidebar-items');

    // [NOTE] Annoying behavior where `Object.entries` converts the keys into strings.
    Object.entries(additions).forEach(([indexStr, ltGraph]) => {
        const index = parseInt(indexStr);

        // Check if there's an existing item with this index.
        const existingItem = document.getElementById(`sidebar-item-${index}`)

        if (existingItem) {
            // [NOTE] Should we remove the animation? and add it back, for it to run?
            // If it exists, remove the `fadeSlideOut` animation.
            existingItem.classList.remove('sidebar-item-remove');

            // Then, add the `fadeSlideIn` one.
            existingItem.classList.add('sidebar-item-new');

            // Plot and store graph at index.
            const container = getRequiredElement<HTMLElement>(`thumbnail-${index}`);

            // [TODO] What happened when it wasn't a copy?
            const graphDataCopy = structuredClone(ltGraph);

            network.sides[index] = new Network(container, graphDataCopy, VIS_SIDE_OPTIONS);

        } else {
            // Creating the thumbnail.
            const item: HTMLDivElement = document.createElement('div');
            item.className = 'sidebar-item';
            item.id = `sidebar-item-${index}`;

            // Add the slide animation.
            item.classList.add('sidebar-item-new');

            // [TODO] The `${index + 1}` could take `n, m` indices from the backend.
            item.innerHTML = `
                <div>Subgraph ${index}</div>
                <div class="sidebar-thumbnail" id="thumbnail-${index}"></div>
                `;

            // Click event.
            item.onclick = function () {
                document.querySelectorAll('.sidebar-item').forEach(el => {
                    el.classList.remove('active');
                });
                item.classList.add('active');
                displayGraph(network, index, delay)
            };

            // Add the thumbnail to the sidebar.
            sidebarItems.appendChild(item);

            // Plot and store graph at index.
            const container = document.getElementById(`thumbnail-${index}`) as HTMLElement;

            // [TODO] What happened when it wasn't a copy?
            const graphDataClone = structuredClone(ltGraph);

            network.sides[index] = new Network(container, graphDataClone, VIS_SIDE_OPTIONS);
        }
    });
}

// Set the sidebar item with highest index as active.
function setActiveItem(network: LTNetwork, index: number,
    state: LTState, delay: number) {
    if (index >= 0) {
        const activeItem = document.getElementById(`sidebar-item-${index}`);

        if (activeItem && state.active !== activeItem) {
            // Disable the last activated sidebar item if different.
            if (state.active) {
                state.active.classList.remove('active');
            }

            // Add active class.
            activeItem.classList.add('active');

            // Display its graph on the main block by default.
            displayGraph(network, index, delay);

            // Save it.
            state.active = activeItem;
        }
    }
}

async function handlePreviews(network: Network, previews: LTId[], delay: number) {
    const nodes = (network as VisNet).body.data.nodes;

    // Highlight next possible nodes.
    const updateProperties = {
        color: {
            background: '#FFFFFF',
            border: '#FFFFFF',
        },
        shadow: {
            enabled: true,
            color: '#FFFFFF',
            size: 10,
            x: 0,
            y: 0,
        },
    };

    const updates = previews.map(id => ({
        id: id,
        ...updateProperties,
    }));

    nodes.update(updates);

    // A slight pause to notice the highlight of the preview nodes.
    await new Promise(resolve => setTimeout(resolve, delay / 2));

    // Revert back to default.
    const resetProperties = {
        color: {
            background: 'lightblue',
            border: 'rgba(255, 255, 255, 0.05)',
        },
        shadow: {
            enabled: false,
        },
    };

    const resets = previews.map(id => ({
        id: id,
        ...resetProperties,
    }));

    nodes.update(resets);
}

function handleMoves(moves: Record<number, LTEdge>, thumbnailGraphs: Network[]) {
    Object.keys(moves).forEach(key => {
        const index = Number(key);

        const indices: Record<string, string> = moves[index];

        if (indices) {
            for (const [fromId, toId] of Object.entries(indices)) {
                // To reverse back to a previous state, we need to keep a {lastVisitedID: ""} after each `deletion`,
                // which breaks the code because the first operation we do after recieving 
                // a VizUpdate instance is `deletion`, thus we move nodes of a deleted graph
                // (`deletion` has to be before `addition` and `moving` has to be before `addition`).
                if (!toId) continue;
                moveHighlight(thumbnailGraphs[index], fromId, toId);
            }
        }
        else {
            throw new Error('No valid transition indices.');
        }
    });
}

export async function updateGraphs(network: LTNetwork, state: LTState,
    updates: LTUpdate, previews: LTId[]) {
    handleDeletions(updates.delu, network.sides);
    handleAdditions(updates.addu, network, state.delay);
    // Get the index of the latest added graph to the thumbnail.
    const index = network.sides.length - 1;
    // Get it active as a sidebar item.
    setActiveItem(network, index, state, state.delay);
    // Show the previews on it.
    await handlePreviews(network.sides[index], previews, state.delay);
    // Finally, move to the next node.
    handleMoves(updates.movu, network.sides);
}

export async function updateFrame(DOM: DOM, network: LTNetwork, state: LTState, newData: LTData) {
    // It's slicing `currentFrame:`.
    const newPreviews: LTId[][] = newData.previews.slice(state.frame);
    const newUpdates: LTUpdate[] = newData.updates.slice(state.frame);

    for (let i: number = 0; i < newUpdates.length; i++) {
        await updateGraphs(network, state, newUpdates[i], newPreviews[i]);
    }

    state.response.data = newData;
    state.frame = newData.updates.length;

    // Update counter.
    DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.frame}`;

    // Update LLM response (fragmented strings allows simple transitions to previous frames).
    DOM.display.llmResponse.value = newData.response.slice(0, state.frame).join('') || "No response available";
}