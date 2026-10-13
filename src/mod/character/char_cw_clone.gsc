// clonewars: SWBF2 clone trooper player body
main()
{
	self detachAll();
	self setModel("cw_clone_body");
	self.voice = "american";
}

precache()
{
	precacheModel("cw_clone_body");
}
