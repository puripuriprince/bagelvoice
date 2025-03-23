"use client";
import { Button } from "@/components/ui/button";

import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import useSourcesStore from "@/stores/useSourcesStore";
import {
	ArrowUturnLeftIcon,
	Bars3Icon,
	DocumentIcon,
	DocumentPlusIcon,
	MicrophoneIcon,
	PhoneArrowUpRightIcon,
} from "@heroicons/react/24/outline";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";

import {
	NewspaperIcon,
	PaperclipIcon,
	PhoneIcon,
	PhoneOff,
} from "lucide-react";
import SourceList from "./SourceList";
import { useParams, useRouter } from "next/navigation";
import useBoothStore from "@/stores/useBoothStore";
import ImportDocument from "./ImportDocument";
import ImportText from "./ImportText";
import ImportMicrophone from "./ImportMicrophone";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import useCallStore, { callOptions } from "@/stores/useCallStore";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogTitle,
	DialogTrigger,
	DialogHeader,
	DialogClose,
} from "@/components/ui/dialog";
import { Card, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import useChatStore from "@/stores/useChatStore";
import { useEffect, useRef, useState } from "react";
import Message from "./Message";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

export default function BoothPage() {
	const { booth_id } = useParams();
	const sources = useSourcesStore(state => state.sources);
	const booth = useBoothStore(state =>
		state.booths.find(x => x.id === parseInt(booth_id)),
	);
	const callReceiver = useCallStore(state => state.callReceiver);
	const setCallReceiver = useCallStore(state => state.setCallReceiver);
	const messages = useChatStore(state => state.messages);
	const messagesContainerRef = useRef(null);
	const isStarted = useChatStore(state => state.isStarted);
	const setIsStarted = useChatStore(state => state.setIsStarted);
	const chatSummary = useChatStore(state => state.chatSummary);
	const setChatSummary = useChatStore(state => state.setChatSummary);
	const addMessage = useChatStore(state => state.addMessage);
	const setSources = useSourcesStore(state => state.setSources);
	const streamMessage = useChatStore(state => state.streamMessage);
	const [isCallActive, setIsCallActive] = useState(false);
	const mediaRecorderRef = useRef(null);
	const streamRef = useRef(null);
	const [startClicked, setStartClicked] = useState(false);

	function handleStartStudying() {
		setStartClicked(true);
		// Get all the summaries from your sources
		const sources = useSourcesStore.getState().sources;

		if (sources.length === 0) {
			alert("Please upload some files first");
			return;
		}

		const summaries = sources
			.filter(source => source.selected)
			.map(source => source.summary);

		// Optional: Show loading state
		// setIsLoading(true);

		fetch(process.env.NEXT_PUBLIC_API_URL + "/meta-summarize", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				summaries: summaries,
				title: "Study Materials",
			}),
		})
			.then(response => {
				if (!response.ok) {
					throw new Error(`HTTP error! Status: ${response.status}`);
				}
				return response.json();
			})
			.then(data => {
				// Set the chat summary with the meta-summary from the backend
				setChatSummary(data.meta_summary);
				setIsStarted(true);
			})
			.catch(error => {
				console.error("Error generating study summary:", error);
				alert(
					"Failed to generate study summary. See console for details.",
				);

				// Fallback to starting anyway without a summary
				setIsStarted(true);
			});
		// .finally(() => {
		//   setIsLoading(false);
		// });
	}

	const [chatBoxInput, setChatBoxInput] = useState("");

	function handleSendMessage() {
		if (chatBoxInput === "") return;

		// Add user message to the chat
		addMessage("Me", chatBoxInput);

		// Get the question from input
		const question = chatBoxInput;

		// Clear input field
		setChatBoxInput("");

		// Get all sources or just selected sources if you have a selection mechanism
		const sources = useSourcesStore.getState().sources;
		// If you have a way to track selected sources, use that instead
		// const selectedSources = sources.filter(source => selectedSourceIds.includes(source.id));

		// Show loading state if needed
		// setIsLoading(true);
		console.log(callOptions.find(x => x.name === callReceiver).description);
		// Call your backend API
		fetch(process.env.NEXT_PUBLIC_API_URL + "/answer-question", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				question: question,
				summaries: sources.map(source => ({
					id: source.id,
					name: source.name,
					summary: source.summary,
				})),
				personality: callOptions.find(x => x.name === callReceiver)
					.description,
			}),
		})
			.then(response => {
				if (!response.ok) {
					throw new Error(`HTTP error! Status: ${response.status}`);
				}
				return response.json();
			})
			.then(data => {
				// Stream the AI's answer with references
				addMessage(
					callReceiver,
					data.answer,
					data.audio
						? process.env.NEXT_PUBLIC_API_URL + data.video
						: null,
				);
				//streamMessage(
				//	"James",
				//	data.answer,
				//	//"/sample-video.mp4", // Keep your video if needed
				//	data.references, // Pass references for citation linking
				//);
			})
			.catch(error => {
				console.error("Error getting answer:", error);
				// Handle error - add an error message to the chat
				addMessage(
					"System",
					"Sorry, I couldn't generate an answer at this time. Please try again.",
				);
			});
		// .finally(() => {
		//   setIsLoading(false);
		// });
	}

	// Function to toggle microphone for call
	const toggleCall = async () => {
		if (isCallActive) {
			// End call and turn off microphone
			if (streamRef.current) {
				streamRef.current.getTracks().forEach(track => track.stop());
				streamRef.current = null;
			}
			if (mediaRecorderRef.current) {
				mediaRecorderRef.current.stop();
				mediaRecorderRef.current = null;
			}
			setIsCallActive(false);
			// You might want to notify the user that the call has ended
		} else {
			try {
				// Request microphone access
				const stream = await navigator.mediaDevices.getUserMedia({
					audio: true,
				});
				streamRef.current = stream;

				// Create media recorder
				const mediaRecorder = new MediaRecorder(stream);
				mediaRecorderRef.current = mediaRecorder;

				// Optional: Handle the recorded audio data
				const audioChunks = [];
				mediaRecorder.addEventListener("dataavailable", event => {
					audioChunks.push(event.data);
				});

				// Start recording
				mediaRecorder.start();
				setIsCallActive(true);

				// Notify the user that the call has started
			} catch (error) {
				console.error("Error accessing microphone:", error);
			}
		}
	};

	useEffect(() => {
		if (messagesContainerRef.current) {
			messagesContainerRef.current.scrollTop =
				messagesContainerRef.current.scrollHeight;
		}
	}, [messages]); // Dependency array includes messages so it runs when messages update

	useEffect(() => {
		// TODO: FETCH THE SOURCES
		setSources([
			//{
			//	id: 1,
			//	name: "Deadlocks",
			//	selected: true,
			//},
			//{
			//	id: 2,
			//	name: "Starvation",
			//	selected: true,
			//},
			//{
			//	id: 3,
			//	name: "Priority Inversion",
			//	selected: true,
			//},
		]);
	}, []);

	// Clean up microphone access when component unmounts
	useEffect(() => {
		return () => {
			if (streamRef.current) {
				streamRef.current.getTracks().forEach(track => track.stop());
			}
		};
	}, []);

	if (!booth) return null;
	return (
		<div className="h-full flex flex-col">
			<h1 className="border-b p-6 flex items-center gap-6 text-2xl font-bold">
				<Link href="/">
					<ArrowUturnLeftIcon className="w-8 h-8 cursor-pointer" />
				</Link>
				{booth.name}
			</h1>
			<div className="flex grow">
				<div className="border-e min-w-xs w-xs">
					<div className="flex items-center justify-between ps-6 pe-3 py-3 border-b">
						<h2 className="font-bold text-xl flex items-center gap-2">
							<PaperclipIcon className="w-6 h-6 " />
							Sources
						</h2>
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button>
									<DocumentPlusIcon size={16} />
								</Button>
							</DropdownMenuTrigger>

							<DropdownMenuContent>
								<ImportDocument />
								<ImportText />
								<ImportMicrophone />
							</DropdownMenuContent>
						</DropdownMenu>
					</div>
					<div className="px-6 mt-2">
						{sources.length === 0 ? (
							<div className="text-white/50">
								Please add sources to continue
							</div>
						) : (
							<>
								<p className="text-white/50">
									Select the sources to include
								</p>
								<SourceList sources={sources} />
								{!isStarted && (
									<Button
										className={"w-full mt-4"}
										onClick={handleStartStudying}
										disabled={startClicked}
									>
										Start Studying
									</Button>
								)}
							</>
						)}
					</div>
				</div>
				<div className="grow flex flex-col">
					{isStarted ? (
						<>
							<div className="px-4 pt-4 grow">
								<div
									className="border rounded-lg w-full overflow-auto"
									ref={messagesContainerRef}
									style={{
										height: "calc(100vh - 250px)",
									}}
								>
									<div className="p-4 text-white/50">
										{chatSummary === "" ? (
											"Summary is being generated, please wait ..."
										) : (
											<ReactMarkdown
												remarkPlugins={[remarkMath]}
												rehypePlugins={[rehypeKatex]}
											>
												{chatSummary}
											</ReactMarkdown>
										)}
									</div>
									<hr className="mx-4" />
									{messages.map(message => (
										<Message
											message={message}
											key={message.id}
										/>
									))}
								</div>
							</div>
							<div className="text-end text-white/80 my-1 me-4 font-semibold">
								{sources.reduce(
									(acc, x) => acc + (x.selected ? 1 : 0),
									0,
								)}{" "}
								sources selected
							</div>
							<div className="min-h-10 w-full px-4 pb-4 flex gap-2">
								<Textarea
									className="h-full"
									value={chatBoxInput}
									onChange={e =>
										setChatBoxInput(e.target.value)
									}
								/>
								<Button
									className="w-20 h-full"
									onClick={handleSendMessage}
								>
									<PaperAirplaneIcon className="w-6 h-6" />
								</Button>
							</div>
						</>
					) : (
						<div className="text-4xl text-white/50 flex items-center justify-center h-full p-10 text-center">
							Select sources and start studying to see the chat
							menu.
						</div>
					)}
				</div>
				<div className="border-s p-6 min-w-xs w-xs">
					<div className="font-bold text-xl">
						<h2 className="font-bold text-xl flex items-center gap-2 mb-4">
							<PhoneIcon className="w-6 h-6 " />
							Voice Call
						</h2>
						<Label>Call Receiver</Label>
						<Dialog>
							<DialogTrigger asChild>
								<Button
									className="w-full mt-2"
									variant={"outline"}
								>
									{callReceiver}
								</Button>
							</DialogTrigger>
							<DialogContent>
								<DialogHeader>
									<DialogTitle>
										Change Call Receiver
									</DialogTitle>
									<DialogDescription>
										Choose your favourite tutor to call.
									</DialogDescription>
									{callOptions.map(option => (
										<DialogClose asChild key={option.name}>
											<Card
												className="w-full p-4 flex gap-2 items-center hover:brightness-125 duration-100 cursor-pointer"
												onClick={setCallReceiver.bind(
													this,
													option.name,
												)}
											>
												<CardTitle>
													{option.name}
												</CardTitle>
												<p className="text-white/50 text-center">
													{option.description}
												</p>
											</Card>
										</DialogClose>
									))}
								</DialogHeader>
							</DialogContent>
						</Dialog>
						<p className="text-sm font-normal text-white/50 mt-2">
							James is a casual teacher who takes teaching
							seriously. He will make sure that you understand the
							topics
						</p>
						<Button
							className={`w-full mt-4 flex gap-3 items-center ${isCallActive ? "bg-red-400 hover:bg-red-500" : ""}`}
							onClick={toggleCall}
						>
							{isCallActive ? (
								<>
									<PhoneOff className="w-6 h-6" />
									End Call
								</>
							) : (
								<>
									<PhoneArrowUpRightIcon className="w-6 h-6" />
									Start Call
								</>
							)}
						</Button>
					</div>
				</div>
			</div>
		</div>
	);
}
