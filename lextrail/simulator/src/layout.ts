import { Network, VisNet, LTNetwork, LTUpdate, LTEdge, LTInterface, LTState } from './types';
import { moveNetwork, referNetwork, cloneContainer, Counter } from './helpers';
import { DOM } from './interface';
import { VIS_MAIN_OPTIONS, VIS_SIDE_OPTIONS } from './render'

function createSidebarElement(index: number): HTMLDivElement {
	const sidebarItems = document.createElement('div');
	sidebarItems.id = `sidebar-items_${index}`;
	sidebarItems.classList.add('sidebar-items');
	return sidebarItems;
}

function createFrontElement(index: number): HTMLDivElement {
	const frontItem = document.createElement('div');
	frontItem.id = `graph-container_${index}`;
	frontItem.classList.add('current-subgraph-container');
	return frontItem;
}

export function initializeLayout(DOM: DOM, state: LTState, length: number): void {
	// Initialize state arrays
	state.networks = Array.from({ length }, () => ({
		front: null,
		sides: [],
	}));
	state.active = Array(length).fill([]);

	// Create DOM elements for each network
	for (let k = 0; k < length; k++) {
		const sidebarItems = createSidebarElement(k);
		DOM.display.currentSidebar.appendChild(sidebarItems);

		const frontItem = createFrontElement(k);
		DOM.display.currentDisplay.appendChild(frontItem);

		state.interfaces.push({
			front: frontItem,
			sides: sidebarItems,
		});
	}
}

export function removeInterface(DOM: DOM, state: LTState, index: number): void {
	const interface_ = state.interfaces[index];
	if (!interface_) {
		throw Error("Deleting a non-existant interface.");
	}

	// Deletes `#sidebar-items_x` and its nested items.
	const sideInterface = interface_.sides;
	if (!sideInterface) {
		throw Error("Deleting a non-existant side interface.");
	}

	interface_.sides.remove();

	// Deletes `#current-graph_x` at the front (nested into `#current-graph`).
	const frontDisplay = interface_.front;
	if (!sideInterface) {
		throw Error("Deleting a non-existant front interface.");
	}

	DOM.display.currentDisplay.removeChild(frontDisplay);

	state.interfaces.splice(index, 1);
	state.active.splice(index, 1);
}

export function removeNetwork(state: LTState, index: number): void {
	const network = state.networks[index];
	if (!network) {
		throw new Error("Deleting a non-existent network.");
	}

	const sideNetwork = network.sides;
	if (!sideNetwork) {
		throw new Error("Deleting a non-existent side network.");
	}

	network.sides.forEach(sideNetwork => sideNetwork.destroy());

	const frontNetwork = network.front;
	if (!frontNetwork) {
		throw new Error("Destroying a non-existent front network.");
	}

	frontNetwork.destroy();

	state.networks.splice(index, 1);
}

export function removePlaceholders(DOM: DOM, state: LTState, index: number): void {
	removeNetwork(state, index);
	removeInterface(DOM, state, index);
}

function cloneInterface(DOM: DOM, state: LTState, index: number): LTInterface {
	const interface_ = state.interfaces[index];
	if (!interface_) {
		throw Error("Cloning a non-existant interface.");
	}

	const interfaceSides = interface_.sides;
	if (!interfaceSides) {
		throw Error("Cloning a non-existant side interface.");
	}

	const interfaceSidesClone = cloneContainer(interfaceSides);

	DOM.display.currentSidebar.appendChild(interfaceSidesClone);

	const interfaceFront = interface_.front;
	if (!interfaceFront) {
		throw Error("Cloning a non-existant front interface.");
	}

	const interfaceFrontClone = cloneContainer(interfaceFront);

	// Brings the cloned front to the main display.
	DOM.display.currentDisplay.appendChild(interfaceFrontClone);

	interfaceFrontClone.classList.add('current-subgraph-container', 'graph-fade');
	interfaceFrontClone.addEventListener('animationend', () => {
		interfaceFrontClone.classList.remove('graph-fade');
	});

	return {
		front: interfaceFrontClone,
		sides: interfaceSidesClone,
	};
}

function cloneNetwork(state: LTState, interfaceClone: LTInterface, index: number) {
	const network = state.networks[index];
	if (!network) {
		throw new Error("Cloning a non-existent network.");
	}

	const sideNetwork = network.sides;
	if (!sideNetwork) {
		throw new Error("Cloning a non-existent side network.");
	}

	const clonedNetworkSides = [];
	for (let i = 0; i < interfaceClone.sides.children.length; i++) {
		// Gets the `#thumbnail-x_y` object.
		const sideElement = interfaceClone.sides.children[i].children[1] as HTMLElement;
		if (!sideElement) {
			throw new Error("Thumbnail not found inside the sidebar item.");
		}

		const clonedNetworkSide = moveNetwork(sideNetwork[i], sideElement, VIS_SIDE_OPTIONS);
		clonedNetworkSides.push(clonedNetworkSide);
	}

	const frontNetwork = network.front;
	if (!frontNetwork) {
		throw new Error("Cloning a non-existant front network.");
	}

	// [NOTE] The front network will NOT be a copy of `frontNetwork`, 
	// `moveNetwork(frontNetwork, interfaceClone.front, VIS_MAIN_OPTIONS);` is not correct.
	// It is a reference to the last (copied) network in the sidebar.
	const referedNetworkFront = referNetwork(clonedNetworkSides.at(-1) as Network, interfaceClone.front, VIS_MAIN_OPTIONS());

	// Automatically set through `setActiveItems`.
	state.active.push([]);

	return {
		front: referedNetworkFront,
		sides: clonedNetworkSides,
	};
}

export function clonePlaceholders(DOM: DOM, state: LTState, index: number): void {
	const clonedInterface = cloneInterface(DOM, state, index);
	state.interfaces.push(clonedInterface);

	const clonedNetwork = cloneNetwork(state, clonedInterface, index);
	state.networks.push(clonedNetwork);

	state.active.push([]);
}

function getChosenIndex(moves: Record<number, LTEdge>, networks: LTNetwork[]): number {
	const maxKey = Math.max(...Object.keys(moves).map(Number));

	// [TODO] Check if TS will return the empty string as `NULL` from Python server.
	// [NOTE] An empty string is considered false in TypeScript.
	let previousId: string | undefined;
	for (let key = maxKey; key >= 0; key--) {
		const move = moves[key];
		if (move?.from) {
			previousId = move.from;
			break;
		}
	}

	if (!previousId) {
		throw new Error("No node has been moved from a valid source.");
	}

	for (let i = 0; i < networks.length; i++) {
		const graph = networks[i].sides.at(-1) as VisNet;

		const highlightedNodes = graph.body.data.nodes.get({
			filter: (node) => {
				if (!node.color || typeof node.color === 'string') return false;
				return node.color.background === '#06b6d4' && node.color.border === '#06b6d4';
			}
		});

		const lastHighlightedNode = highlightedNodes[0];
		if (lastHighlightedNode && previousId === lastHighlightedNode.id) {
			return i;
		}
	}

	throw new Error("No matching highlighted node found in any network.");
}

export function updateLayout(DOM: DOM, state: LTState, prevLength: number, updates: LTUpdate[]): void {
	const chosenIndices = updates.map(update =>
		getChosenIndex(update.movu, state.networks)
	);

	for (const [key, count] of Object.entries(Counter(chosenIndices, prevLength - 1))) {
		const index = parseInt(key);

		if (count === 0) {
			removePlaceholders(DOM, state, index);
		} else if (count > 1) {
			for (let i = 0; i < count - 1; i++) {
				clonePlaceholders(DOM, state, index);
			}
		}
	};
}