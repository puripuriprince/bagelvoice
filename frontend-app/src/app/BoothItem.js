import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

import moment from "moment";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardHeader,
	CardTitle,
	CardDescription,
	CardContent,
} from "@/components/ui/card";
import { PencilIcon, TrashIcon } from "lucide-react";
import Link from "next/link";
import { Form, FormField } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import useBoothStore from "@/stores/useBoothStore";

export default function BoothItem({ booth }) {
	const [boothNameInput, setBoothNameInput] = useState("");

	const renameBooth = useBoothStore(state => state.renameBooth);
	const deleteBooth = useBoothStore(state => state.deleteBooth);

	function onRenameBooth() {
		if (!boothNameInput) return;
		renameBooth(booth.id, boothNameInput);
	}

	function onDeleteBooth() {
		deleteBooth(booth.id);
	}

	return (
		<Card>
			<Link href={`/booth/${booth.id}`}>
				<CardHeader className={"hover:underline cursor-pointer"}>
					<CardTitle>{booth.name}</CardTitle>
					<CardDescription>
						{moment(booth.timestamp).fromNow()} •{" "}
						{booth.source_count} sources
					</CardDescription>
				</CardHeader>
			</Link>
			<CardContent className={"grid grid-cols-2 gap-2"}>
				<AlertDialog onOpenChange={x => !x && setBoothNameInput("")}>
					<AlertDialogTrigger asChild>
						<Button className={"cursor-pointer"}>
							<PencilIcon size={16} />
							Rename
						</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>
								Rename booth - {booth.name}
							</AlertDialogTitle>
							<AlertDialogDescription>
								<Input
									placeholder={"Enter new name"}
									value={boothNameInput}
									onChange={e =>
										setBoothNameInput(e.target.value)
									}
								/>
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel>Cancel</AlertDialogCancel>
							<AlertDialogAction onClick={onRenameBooth}>
								Rename
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>

				<AlertDialog onOpenChange={x => !x && setBoothNameInput("")}>
					<AlertDialogTrigger asChild>
						<Button
							variant={"destructive"}
							className={"cursor-pointer"}
						>
							<TrashIcon size={16} />
							Delete
						</Button>
					</AlertDialogTrigger>
					<AlertDialogContent>
						<AlertDialogHeader>
							<AlertDialogTitle>
								Delete booth - {booth.name}
							</AlertDialogTitle>
							<AlertDialogDescription>
								This action cannot be undone. Are you sure you
								want to delete this booth?
							</AlertDialogDescription>
						</AlertDialogHeader>
						<AlertDialogFooter>
							<AlertDialogCancel>No, cancel</AlertDialogCancel>
							<AlertDialogAction asChild>
								<Button
									variant={"destructive"}
									onClick={onDeleteBooth}
									className={"text-white"}
								>
									Yes, delete
								</Button>
							</AlertDialogAction>
						</AlertDialogFooter>
					</AlertDialogContent>
				</AlertDialog>
			</CardContent>
		</Card>
	);
}
