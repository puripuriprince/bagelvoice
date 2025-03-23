import { create } from "zustand";
const BOOTHS_KEY = "booths-key";

// TODO: Implement CRUD operations
const useBoothStore = create(set => ({
	booths: [],
	//	// Dummy data for now
	//	{
	//		id: 1,
	//		name: "adasd",
	//		source_count: 3,
	//		timestamp: new Date("2021-09-01"),
	//	},
	//	{
	//		id: 2,
	//		name: "math 202",
	//		source_count: 5,
	//		timestamp: new Date("2025-03-01"),
	//	},
	//	{
	//		id: 3,
	//		name: "comp 346",
	//		source_count: 1,
	//		timestamp: new Date("2025-03-10"),
	//	},
	//],
	setBooths: booths => set({ booths }),

	createBooth: async booth => {
		set(state => ({
			booths: [
				...state.booths,
				{
					// TODO: make the id supplied from the backend
					id: parseInt(Math.random() * 100_000),
					timestamp: new Date(),
					source_count: 0,
					...booth,
				},
			],
		}));
	},
	renameBooth: async (id, name) => {
		set(state => ({
			booths: state.booths.map(booth =>
				booth.id === id ? { ...booth, name } : booth,
			),
		}));
	},
	deleteBooth: async id => {
		set(state => ({
			booths: state.booths.filter(booth => booth.id !== id),
		}));
	},
}));

// check if we're client

if (typeof window !== "undefined") {
	// Load booths from local storage
	const localBooths = localStorage.getItem(BOOTHS_KEY);
	if (localBooths) {
		useBoothStore.setState({ booths: JSON.parse(localBooths) });
	}

	useBoothStore.subscribe(state => {
		localStorage.setItem(BOOTHS_KEY, JSON.stringify(state.booths));
	});
}

export default useBoothStore;
