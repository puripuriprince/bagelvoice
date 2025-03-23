import { create } from "zustand";

const useChatStore = create((set, get) => ({
	messages: [
		//{ id: 1, user: "Me", message: "Hi, how is your day doing?" },
		//{
		//	id: 2,
		//	user: "Alex",
		//	message:
		//		"Hey! My day's going great—thanks for asking. How about you? Working on anything interesting today? 😊",
		//	video: "sample.mp4",
		//},
		//{
		//	id: 3,
		//	user: "Me",
		//	message:
		//		"not sure, can you tell me more about what i should do in life",
		//},
		//{
		//	id: 4,
		//	user: "Alex",
		//	message:
		//		"Of course! I'd be happy to help. What are you passionate about? What are your interests?",
		//},
		//{
		//	id: 5,
		//	user: "Alex",
		//	message:
		//		"I think it's important to find something you're passionate about and pursue it. What do you think?",
		//},
	],
	isStarted: false,
	setIsStarted: isStarted => set({ isStarted }),
	chatSummary: "",
	setChatSummary: chatSummary => set({ chatSummary }),
	addMessage: (user, message, video) => {
		const newId = get().messages.length + 1;
		set(state => ({
			messages: [...state.messages, { id: newId, user, message, video }],
		}));
	},

	//// Add fake streaming functionality
	streamMessage: (user, fullMessage, video) => {
		// Create a new message with empty content
		const newId = get().messages.length + 1;
		set(state => ({
			messages: [
				...state.messages,
				{ id: newId, user, message: "", video },
			],
		}));

		// Split the message into words
		const words = fullMessage.split(" ");
		let currentIndex = 0;

		// Set up interval to add words
		const intervalId = setInterval(() => {
			if (currentIndex < words.length) {
				// Get the current messages
				const currentMessages = get().messages;
				const lastMessage = currentMessages[currentMessages.length - 1];

				// Add the next word (with a space if not the first word)
				const updatedMessage =
					lastMessage.message === ""
						? words[currentIndex]
						: lastMessage.message + " " + words[currentIndex];

				// Update the message
				set(state => ({
					messages: state.messages.map(msg =>
						msg.id === newId
							? { ...msg, message: updatedMessage }
							: msg,
					),
				}));

				currentIndex++;
			} else {
				// Clear interval when all words have been added
				clearInterval(intervalId);
			}
		}, 50);

		// Return a function to cancel streaming if needed
		return () => clearInterval(intervalId);
	},
}));

//useChatStore
//	.getState()
//	.streamMessage(
//		"Alex",
//		"This is a test message that will appear word by word every 100 milliseconds to simulate a streaming effect for your chat interface. This message is quite long, so it should take a while to fully appear. Enjoy! 😊 this is about 1000 words. So, it should take about 10 seconds to fully appear.",
//	);
export default useChatStore;
