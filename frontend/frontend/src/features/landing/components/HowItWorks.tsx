export const HowItWorks = () => {
  return (
    <section className="py-20 bg-gray-50 bg-grid">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900 font-mono">
          <span className="text-accent">&gt;</span> How to Play
        </h2>
        <p className="mt-4 text-center text-base text-gray-600 max-w-xl mx-auto">
          Simple steps to start influencing conversations and uncovering secrets.
        </p>
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4 items-start">
          <div className="text-center space-y-3 p-5 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex items-center justify-center h-10 w-10 rounded mx-auto bg-accent/10 text-accent font-mono text-sm border border-accent/30">01</div>
            <h3 className="font-mono text-sm tracking-wider text-gray-800">Join the Room</h3>
            <p className="text-xs text-gray-600 leading-relaxed">Create a private room or join your friends using a room code.</p>
          </div>
          <div className="text-center space-y-3 p-5 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex items-center justify-center h-10 w-10 rounded mx-auto bg-accent/10 text-accent font-mono text-sm border border-accent/30">02</div>
            <h3 className="font-mono text-sm tracking-wider text-gray-800">Get Your Role</h3>
            <p className="text-xs text-gray-600 leading-relaxed">Become the Coordinator, Detective, or Citizen with secret objectives.</p>
          </div>
          <div className="text-center space-y-3 p-5 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex items-center justify-center h-10 w-10 rounded mx-auto bg-accent/10 text-accent font-mono text-sm border border-accent/30">03</div>
            <h3 className="font-mono text-sm tracking-wider text-gray-800">Talk &amp; Observe</h3>
            <p className="text-xs text-gray-600 leading-relaxed">Chat naturally while completing objectives and watching for suspicious behavior.</p>
          </div>
          <div className="text-center space-y-3 p-5 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex items-center justify-center h-10 w-10 rounded mx-auto bg-accent/10 text-accent font-mono text-sm border border-accent/30">04</div>
            <h3 className="font-mono text-sm tracking-wider text-gray-800">Accuse &amp; Reveal</h3>
            <p className="text-xs text-gray-600 leading-relaxed">Vote for the suspected Coordinator and discover who was manipulating the conversation.</p>
          </div>
        </div>
      </div>
    </section>
  )
}
