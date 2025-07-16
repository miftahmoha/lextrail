import { VisNet, LTId, LTEdge, LTGraph, LTUpdate, LTData, LTNetwork, LTState, Network, LTNetworkA, LTInterface, Optional } from './types'
import { getRequiredElement, cloneContainer, cloneNetwork, cloneNetwork_ } from './helpers';
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
// function displayGraph(network: LTNetworkA, index: number, delay: number, section: number) {
//     const mainContainer = getRequiredElement<HTMLElement>('current-graph')

//     // Allows a vertical layout within the container.
//     // [TODO] Add it a single time.
//     mainContainer.classList.add('current-graph-container');

//     // Get the container at the section.
//     let subContainer = document.getElementById(`graph-container-${section}`) as HTMLElement | null;
//     if (!subContainer) {
//         // subContainer = document.createElement('div');
//         // subContainer.id = `current-subgraph-${section}`
//         // // [TODO] Needed?
//         // subContainer.classList.add('current-subgraph-container');
//         // // Add fade class.
//         // subContainer.classList.add('graph-fade');
//         // mainContainer.appendChild(subContainer);
//         throw Error("Should exist from copying..");
//     }

//     // Remove the class after animation completes, if it stays, the animation will not
//     // happen since we're we'll be adding an existant animation class in the next frame.
//     setTimeout(() => {
//         subContainer.classList.remove('graph-fade');
//     }, delay / 2);

//     // Get the network instance at index.
//     const networkInstance = network.sides[section][index];

//     // Get its nodes and edges then build a clone.
//     // [TODO] Use a reference and not a copy. 
//     const graphDataClone = {
//         nodes: (networkInstance as VisNet).body.data.nodes,
//         edges: (networkInstance as VisNet).body.data.edges,
//     } as any;

//     // [NOTE] Check if optimization leads to undefined behavior.
//     // let networkFront = network.front;

//     // if (network.front[section]) {
//     //     network.front[section].setData(graphDataClone);
//     //     network.front[section].setOptions({
//     //         nodes: {
//     //             font: {
//     //                 color: DOM.root.classList.contains('light-mode') ? '#000000' : '#ffffff'
//     //             }
//     //         }
//     //     });
//     // } else {
//     network.front[section] = new Network(subContainer, graphDataClone, VIS_MAIN_OPTIONS);
//     // }

//     const status = getRequiredElement('status');
//     status.innerHTML = `Displaying Subgraph ${+index + 1} of ${network.sides.length}`;
// }


// Moves the highlight from a node A to a node B.
async function moveHighlight(network: Network, fromId: string, toId: string): Promise<void> {
    // [TODO] Add a check that `fromNode` should be in a highlighted state if not null.
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


async function handleDeletions(deletions: Record<number, LTGraph>, interface_: LTInterface, network: LTNetwork, delay: number) {
    // Delete from highest to lowest to avoid index shifts in `network.splice(index, 1)`.
    const indicesToDelete: number[] = Object.keys(deletions).map(Number).sort((a, b) => b - a);

    // Then 
    indicesToDelete.forEach(index => {
        const sidebarItem = interface_.sides.children[index];
        if (!sidebarItem) {
            throw Error(`Deleting an inexistant sidebar item at ${index}.`);
        }

        // [NOTE] Need to delete the class to be able to trigger the animation in next frames.
        sidebarItem.classList.add('sidebar-item-remove');
        sidebarItem.addEventListener('animationend', () => {
            sidebarItem.remove();
        });

        // [NOTE] No need to reason about `frontDisplay` since it's going to be updated to the last item by `setActiveItems`.
        const sideNetworks = network.sides;

        const sideNetwork = network.sides[index];
        if (!sideNetwork) {
            throw Error(`Deleting an inexistant network at ${index}.`);
        }
        else {
            sideNetwork.destroy();
            sideNetworks.splice(index, 1);
        }

        // [NOTE] `sidebar-item-remove` will take care of hiding the object, avoiding to create it again.
        // interface_.sides.removeChild(sidebarItem);
    });
}


async function handleAdditions(additions: Record<number, LTGraph>, interface_: LTInterface, network: LTNetwork, delay: number) {
    // [NOTE] `Object.entries` implicitly converts the keys into a string.
    Object.entries(additions).forEach(([sindex, graphData]) => {
        const index = parseInt(sindex);

        // [TODO] Only pass `interface_.sides` as argument.
        const sideDisplay = interface_.sides;

        // Check if there's an existing item with this index.
        const sidebarItem = sideDisplay.children[index];

        if (sidebarItem) {
            // [TODO] This class is never added, does it animate through removal? Is it uneccesary? Should it be an `.add`?
            // [NOTE] Animation will not be triggered with an existant class, removal is necessary since it could have vbe
            sidebarItem.classList.remove('sidebar-item-remove');
            sidebarItem.classList.add('sidebar-item-new');

            // `2 * index + 1` since each thumbnail has a division above it containing a header.
            const thumbnailItem = sidebarItem.children[2 * index + 1] as Optional<HTMLElement>;
            if (!thumbnailItem) throw Error("Thumbnail item is not found inside sidebar item.")

            // [TODO] Check if copy is necessary.
            network.sides[index] = new Network(thumbnailItem, structuredClone(graphData), VIS_SIDE_OPTIONS);
        } else {
            // [NOTE] Elements of an ambiguous section have a suffix `#NUMBER` which specifies the numbering.
            // [NOTE] When the interface is cloned, a check is run on the elements to ensure the right format.
            const number = parseInt(sideDisplay.id.split('_')[1]);

            const sidebarItem = document.createElement('div');
            sidebarItem.className = 'sidebar-item';
            sidebarItem.id = `sidebar-item-${index}_${number}`;
            sidebarItem.classList.add('sidebar-item-new');

            const label = document.createElement("div");
            label.id = `label-${index}_${number}`;
            label.textContent = `Subgraph ${index}`;

            const thumbnail = document.createElement("div");
            thumbnail.className = "sidebar-thumbnail";
            thumbnail.id = `thumbnail-${index}_${number}`;

            sidebarItem.append(label, thumbnail);

            sideDisplay.appendChild(sidebarItem);

            sidebarItem.classList.add('graph-fade');
            setTimeout(() => {
                sidebarItem.classList.remove('graph-fade');
            }, delay / 2);

            sidebarItem.onclick = function () {
                [...sideDisplay.children].forEach(child => child.classList.remove('active'));
                sidebarItem.classList.add('active');

                // const frontDisplay = interface_.front.children
                // if (frontDisplay.length > 1) {
                //     throw Error(`The front interface at section ${number} has more than one child.`);
                // }

                const frontItem = interface_.front;

                network.front = cloneNetwork(network.sides[index], (frontItem as HTMLElement), VIS_MAIN_OPTIONS);

                // [NOTE] Need to delete the class to be able to trigger the animation in next frames.
                frontItem.classList.add('graph-fade');
                setTimeout(() => {
                    frontItem.classList.remove('graph-fade');
                }, delay / 2);
            };

            // [TODO] Check if copy is necessary.
            network.sides.push(new Network(thumbnail, structuredClone(graphData), VIS_SIDE_OPTIONS));
        }
    });
}

// Set the sidebar item with highest index as active.
async function setActiveItem(interface_: LTInterface, network: LTNetwork, active: HTMLElement[], delay: number) {

    const activeItem = [...interface_.sides.children].at(-1) as HTMLElement;

    const lastActiveItem = active[0];

    if (activeItem && lastActiveItem !== activeItem) {
        // Disable the last activated sidebar item if different.
        if (lastActiveItem) {
            lastActiveItem.classList.remove('active');
        }

        // Add active class.
        activeItem.classList.add('active');

        // const frontDisplay = interface_.front.children
        // if (frontDisplay.length > 1) {
        //     throw Error(`The front interface has more than one child.`);
        // }

        const lastNetwork = network.sides.at(-1);
        if (!lastNetwork) {
            throw Error(`Inexistant network.`);
        }

        // const frontItem = frontDisplay[0];
        const frontItem = interface_.front;

        network.front = cloneNetwork_(lastNetwork, (frontItem as HTMLElement), VIS_MAIN_OPTIONS);

        // [NOTE] Need to delete the class to be able to trigger the animation in next frames.
        frontItem.classList.add('graph-fade');
        setTimeout(() => {
            frontItem.classList.remove('graph-fade');
        }, delay / 2);
    };

    // Save it.
    active[0] = activeItem;
}


async function handlePreviews(network: LTNetwork, previews: LTId[], delay: number) {
    const frontNetwork = network.front;
    if (!frontNetwork) {
        throw Error("Inexistant front network after `setActiveItem` call.")
    }

    const nodes = (frontNetwork as VisNet).body.data.nodes;

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

async function handleMoves(moves: Record<number, LTEdge>, network: LTNetwork) {
    for (const [sindex, move] of Object.entries(moves)) {
        if (!move.to) continue;
        const index = Number(sindex);
        const sideNetwork = network.sides;
        await moveHighlight(sideNetwork[index], move.from, move.to);
    }
}

export async function updateGraphs(state: LTState, updates: LTUpdate[], previews: LTId[]) {
    const promises = updates.map(async (update, i) => {
        await handleDeletions(update.delu, state.interfaces[i], state.networks[i], state.delay);
        await handleAdditions(update.addu, state.interfaces[i], state.networks[i], state.delay);
        await setActiveItem(state.interfaces[i], state.networks[i], state.active[i], state.delay);
        // await handlePreviews(state.networks[i], previews, state.delay);
        await handleMoves(update.movu, state.networks[i]);
    });

    await Promise.all(promises);

}

function getLastMovedNode(moves: Record<number, LTEdge>): LTId {
    let maxKey = Math.max(...Object.keys(moves).map(Number));

    // [TODO] Check if TS will return the empty string as `NULL` from Python server.
    // [NOTE] An empty string is considered false in TypeScript.
    let previousId = moves[maxKey].from;
    while (!previousId) {
        maxKey -= 1;
        previousId = moves[maxKey].from;

        if ((maxKey === 0) && !previousId) {
            throw Error("Ambiguity resolved with no node movement.")
        }
    }

    return previousId
}

function getNodeSection(previousId: LTId, networks: LTNetwork[]) {
    for (let j = 0; j < networks.length; j++) {
        const graph = networks[j].sides.at(-1);

        const lastHighlightedNode = (graph as VisNet).body.data.nodes.get({
            filter: function (node) {
                if (!node.color) return false;
                else if (typeof node.color === 'string') return false;
                // Handles `Color` type.
                return node.color.background === '#06b6d4' && node.color.border === '#06b6d4';
            }
        })[0];
        if (previousId === lastHighlightedNode.id) {
            return j;
        }
    }

    throw Error("The last highlighted node is non-existent inside the networks.");
}

function countOccurrences(arr: number[], maxValue: number): Record<number, number> {
    const occurrences: Record<number, number> = {};

    for (let i = 0; i <= maxValue; i++) {
        occurrences[i] = 0;
    }

    for (const num of arr) {
        if (num >= 0 && num <= maxValue) {
            occurrences[num]++;
        }
    }

    return occurrences;
}

// [TODO] Need to clone the `state.active` and move the equivalent cloned element into it.
function ambiguate(interfaces: LTInterface[], networks: LTNetwork[], actives: HTMLElement[][], occurences: Record<number, number>, delay: number): void {
    Object.entries(occurences).forEach(([sindex, count]) => {
        const section = parseInt(sindex);

        const mainContainer = getRequiredElement<HTMLElement>('current-graph');

        // [TODO] Need to remove the network from the list networks.
        if (count == 0) {
            const network = networks[section];

            const interfaceToRemove = interfaces[section];

            for (const networkToRemove of network.sides) {
                networkToRemove.destroy();
            }
            interfaceToRemove.sides.remove();

            mainContainer.removeChild(interfaceToRemove.front);

            const networkToRemove = network.front;
            if (!networkToRemove) {
                throw Error("Destroying an non-existant front network.")
            }

            networkToRemove.destroy();
            interfaceToRemove.front.remove();

            // Remove the network from the networks.
            networks.splice(section, 1);
            interfaces.splice(section, 1);
            // Remove the active element.
            actives.splice(section, 1);
        }
        if (count > 1) {
            const networkToClone = networks[section];

            const interfaceToClone = interfaces[section];

            for (let k = 1; k < count; k++) {
                const interfaceSides = cloneContainer(interfaceToClone.sides);

                // Need to bring the cloned front to the main display.
                const interfaceFront = cloneContainer(interfaceToClone.front);
                mainContainer.appendChild(interfaceFront);

                interfaceFront.classList.add('current-subgraph-container');
                interfaceFront.classList.add('graph-fade');
                setTimeout(() => {
                    interfaceFront.classList.remove('graph-fade');
                }, delay / 2);

                interfaces.push({
                    front: interfaceFront,
                    sides: interfaceSides,
                });

                const networkFront = networkToClone.front;
                if (!networkFront) {
                    throw Error("Network front is non-existant.");
                }
                const networkSides = networkToClone.sides;

                const clonedNetworkFront = cloneNetwork(networkFront, interfaceFront, VIS_MAIN_OPTIONS);
                const clonedNetworkSides = [];

                for (let l = 0; l < interfaceSides.children.length; l++) {
                    // [NOTE] The network is cloned along the thumbnail, each `sidebare-item-index_X` inside `interfaceSides`
                    // has (1) a header, then (2) the thumbnail element.
                    clonedNetworkSides.push(cloneNetwork(networkSides[l], (interfaceSides.children[l].children[1] as HTMLElement), VIS_SIDE_OPTIONS));
                }

                networks.push({ front: clonedNetworkFront, sides: clonedNetworkSides });

                // Clone the actives.
                actives.push([]);

            }
        }
    })
}

// [TODO] Treat a case where currlen == prevlen but prevlen > 1, since it leads to if one the choices duplicated to
// move a node to a highlighted state and that node was not highlighted before.
export async function updateFrame(DOM: DOM, state: LTState, newData: LTData) {
    const newPreviews: LTId[][] = newData.previews.slice(state.frame);
    const newUpdates: LTUpdate[][] = newData.updates.slice(state.frame);

    for (let i = 0; i < newUpdates.length; i++) {
        // Dealing with ambiguous symbols.
        const currlen = newUpdates[i].length;
        const prevlen = state.networks.length;
        const updates = newUpdates[i];

        // If `offset != 0` means either (1) we've got an ambiguity and we've got to render every path,
        // or (2) we've come from one and we've got to render the chosen path.
        const offset = currlen - prevlen;

        // First iteration, deals with initial ambiguity.
        if (prevlen === 0) {
            // networks.front = Array(currlen).fill(null);
            // networks.sides = Array(currlen).fill([]);
            state.networks = Array.from({ length: currlen }, () => ({
                front: null,
                sides: [],
            }));
            state.active = Array(currlen).fill([]);
            const mainContainer = getRequiredElement<HTMLElement>('current-graph');
            const mainSidebar = getRequiredElement<HTMLElement>('sidebar-items');
            // for (let k = 1; k < currlen; k++) {
            //     const front = cloneContainer(state.interfaces[k - 1].front)
            //     mainContainer.appendChild(front)
            //     cloneContainer(state.interfaces[k].sides)
            // }

            for (let k = 0; k < currlen; k++) {
                const sidebarItems = document.createElement('div');
                sidebarItems.id = `sidebar-items_${k}`;
                sidebarItems.classList.add('sidebar-items');
                mainSidebar.appendChild(sidebarItems);
                const frontItem = document.createElement('div');
                frontItem.id = `graph-container_${k}`;
                frontItem.classList.add('current-subgraph-container');
                mainContainer.appendChild(frontItem)
                state.interfaces.push({
                    front: frontItem,
                    sides: sidebarItems,
                });
            }
        }

        // Check if last update was ambiguous, if that's the case, then to clean the unchosen path.
        else if (offset !== 0 || offset == 0) {
            let concreteIndices: number[] = [];
            for (let j = 0; j < updates.length; j++) {
                const moves = updates[j].movu;

                const previousId = getLastMovedNode(moves);

                const section = getNodeSection(previousId, state.networks);

                concreteIndices.push(section);
            }
            // Check the front's children to be > 1 does not make sense (it's one single object), we must check the children of the main display
            // and it should be equal to newUpdates[i].length.
            // Where is the logic for removal?

            const occurrences = countOccurrences(concreteIndices, prevlen - 1);

            // Get indices which will be deleted, or cloned 0 times and in ambiguate function when count is 0, remove the interface
            // the network.

            ambiguate(state.interfaces, state.networks, state.active, occurrences, state.delay);
        }

        await updateGraphs(state, newUpdates[i], newPreviews[i]);
    }

    state.response.data = newData;
    state.frame = newData.updates.length;

    // Update counter.
    DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.frame}`;

    // Update LLM response (fragmented strings allows simple transitions to previous frames).
    DOM.display.llmResponse.value = newData.response.slice(0, state.frame).join('') || "No response available";
}
