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

export default function BoothPage() {
	const { booth_id } = useParams();
	const sources = useSourcesStore(state => state.sources);
	const booth = useBoothStore(state =>
		state.booths.find(x => x.id === parseInt(booth_id)),
	);
	const callReceiver = useCallStore(state => state.callReceiver);
	const setCallReceiver = useCallStore(state => state.setCallReceiver);

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
							style={{
								height: "calc(100vh - 200px)",
							}}
						>
							<div className="p-4">
								<div className="flex gap-4 items-center">
									<h2 className="font-bold text-green-400">
										Me
									</h2>
								</div>
								<p className="mt-2">
									Hi, how is your day doing?
								</p>
							</div>
							<div className="p-4">
								<div className="flex gap-4 items-center">
									<img className="rounded-full w-12 h-12 bg-white" />
									<h2 className="font-bold">Alex</h2>
								</div>
								<p className="mt-2">
									Hey! My day's going great—thanks for asking.
									How about you? Working on anything
									interesting today? 😊
								</p>
							</div>

							<div className="p-4">
								<div className="flex gap-4 items-center">
									<h2 className="font-bold text-green-400">
										Me
									</h2>
								</div>
								<p className="mt-2">
									not sure, can you tell me more about what i
									should do in life
								</p>
							</div>

							<div className="p-4">
								<div className="flex gap-4 items-center">
									<img className="rounded-full w-12 h-12 bg-white" />
									<h2 className="font-bold">Alex</h2>
								</div>
								<p className="mt-2">
									That’s a really deep question! Figuring out
									what to do in life can feel overwhelming at
									times, but it’s also a chance to explore
									what excites you. Here are a few things that
									might help guide you in finding direction:
									Identify What You're Passionate About: Think
									about what excites you. Whether it's
									technology, art, helping others, or
									something else, knowing what you’re
									passionate about can give you a sense of
									purpose. Set Small Goals: Sometimes, big
									goals can be intimidating. Start by setting
									smaller, achievable goals that can gradually
									lead you toward your bigger dreams. Learn
									Continuously: Life is full of learning
									opportunities. Whether it's through school,
									hobbies, or life experiences, gaining new
									skills and knowledge is a great way to grow.
									Explore Different Paths: It’s okay to not
									have it all figured out. Try different
									things, whether through internships, side
									projects, or new hobbies. Exploration can
									help you discover things you never thought
									you'd enjoy. Be Open to Change: Life is
									unpredictable. Be open to changing
									directions as you grow and learn more about
									yourself. Sometimes, the best opportunities
									come from unexpected places. Take Care of
									Yourself: Don’t forget to nurture your
									physical and mental health. Life can be
									busy, but feeling good is essential to
									living well. Impact and Meaning: Think about
									what kind of impact you want to make. It
									could be through work, relationships, or
									contributing to something bigger than
									yourself. Do any of these resonate with you?
									Sometimes just thinking about what feels
									meaningful can spark new ideas.
								</p>
							</div>
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
