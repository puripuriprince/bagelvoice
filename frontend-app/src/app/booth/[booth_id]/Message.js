import { useState, useEffect } from "react";

export default function Message({ message }) {
	const [videoExists, setVideoExists] = useState(false);

	useEffect(() => {
		if (message.video) {
			const checkVideoExistence = async () => {
				try {
					const response = await fetch(message.video, {
						method: "HEAD",
					});
					if (response.ok) {
						setVideoExists(true);
					} else {
						setVideoExists(false);
					}
				} catch (error) {
					console.error("Error checking video:", error);
					setVideoExists(false);
				}
			};

			const intervalId = setInterval(checkVideoExistence, 5000); // Poll every 5 seconds
			checkVideoExistence(); // Check immediately as well

			// Cleanup interval on component unmount or when video is found
			return () => clearInterval(intervalId);
		}
	}, [message.video]);

	return (
		<div className="p-4" key={message.id}>
			<div className="flex gap-4 items-center">
				{message.user !== "Me" && (
					<img className="rounded-full w-12 h-12 bg-white" />
				)}
				<h2
					className={`font-bold ${message.user === "Me" && "text-green-400"}`}
				>
					{message.user}
				</h2>
			</div>
			<p className="mt-2">{message.message}</p>
			{message.video && videoExists && (
				<video
					type="video/mp4"
					src={message.video}
					controls
					autoPlay
					className="w-full mt-2"
				/>
			)}
			{!videoExists && message.video && (
				<div className="w-full h-[300px] border rounded-lg bg-neutral-900 p-4 mt-2 font-bold flex items-center justify-center">
					<p>A video is being processed, please wait ...</p>
				</div>
			)}
		</div>
	);
}
