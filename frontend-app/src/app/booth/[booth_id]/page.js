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

import { NewspaperIcon, PaperclipIcon, PhoneIcon } from "lucide-react";
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
import { useEffect, useRef } from "react";

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

	useEffect(() => {
		if (messagesContainerRef.current) {
			messagesContainerRef.current.scrollTop =
				messagesContainerRef.current.scrollHeight;
		}
	}, [messages]); // Dependency array includes messages so it runs when messages update

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
						<p className="text-white/50">
							Select the sources to include
						</p>
						{sources.length === 0 ? (
							<div></div>
						) : (
							<SourceList sources={sources} />
						)}
					</div>
				</div>
				<div className="grow flex flex-col">
					<div className="px-4 pt-4 grow">
						<div
							className="border rounded-lg w-full overflow-auto"
							ref={messagesContainerRef}
							style={{
								height: "calc(100vh - 200px)",
							}}
						>
							{messages.map(message => (
								<div className="p-4" key={message.id}>
									<div className="flex gap-4 items-center">
										{message.user !== "Me" && (
											<img
												className={`rounded-full w-12 h-12 bg-white`}
											/>
										)}
										<h2
											className={`font-bold ${message.user === "Me" && "text-green-400"}`}
										>
											{message.user}
										</h2>
									</div>
									<p className="mt-2">{message.message}</p>
								</div>
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
						<Textarea className="h-full" />
						<Button className="w-20 h-full">
							<PaperAirplaneIcon className="w-6 h-6" />
						</Button>
					</div>
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
						<Button className="w-full mt-4 flex gap-3 items-center">
							<PhoneArrowUpRightIcon className="w-6 h-6" />
							Start Call
						</Button>
					</div>
				</div>
			</div>
		</div>
	);
}
