import { create } from "zustand";

export const callOptions = [
	{
		name: "James",
		description:
			"James is a casual teacher who takes teaching seriously. He will make sure that you understand the topics",
	},
	{
		name: "Alex",
		description:
			"Alex likes to use Gen-Z slang to make sure you understand the topics. He is a cool teacher.",
	},
	{
		name: "John",
		description:
			"John might insult you when you make mistakes, but he is a good teacher. He truly cares about your learning.",
	},
];
const useCallStore = create(set => ({
	callReceiver: "John",
	setCallReceiver: receiver => set({ callReceiver: receiver }),
}));

export default useCallStore;
