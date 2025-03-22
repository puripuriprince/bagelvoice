import { create } from "zustand";

const useBoothStore = create(set => ({
	booths: [
		{
			id: 1,
			name: "adasd",
			source_count: 3,
			timestamp: new Date("2021-09-01"),
		},
	],
	setBooths: booths => set({ booths }),

	createBooth: async booth => {
		set(state => ({ booths: [...state.booths, booth] }));
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

export default useBoothStore;
