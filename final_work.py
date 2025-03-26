import networkx as nx
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import simpledialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os

class SocialNetwork:
    """A class representing a user's personal social network."""
    def __init__(self, username):
        self.username = username
        self.following = set()
        self.followers = set()
        # Expanded default user set
        self.all_users = {"Logical", "Siaw", "Ama", "user4", "user5", "user6", "user7", "user8", "user9", "user10"}
        self.all_users.add(username)
    
    def follow(self, user):
        """Follow a user if they exist and are not the current user."""
        if user != self.username and user in self.all_users:
            self.following.add(user)
            return True
        return False
    
    def unfollow(self, user):
        """Unfollow a user if they are in the following set."""
        if user in self.following:
            self.following.remove(user)
            return True
        return False

class SocialNetworkApp:
    def __init__(self):
        # Initialize the main window
        self.root = ctk.CTk()
        self.root.title("Social Network - User Profile")
        self.root.geometry("1200x700")
        ctk.set_appearance_mode("Dark")
        
        # Application state
        self.network = None
        self.username = None
        self.all_users_data = {}
        
        # Initialize data
        self.load_all_users()
        
        # Create initial user selection window
        self.create_user_selection()
    
    def create_dashboard(self):
        """Create the main dashboard for the selected user."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main dashboard frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Sidebar
        sidebar = ctk.CTkFrame(main_frame, width=250)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)
        
        # Profile header
        profile_label = ctk.CTkLabel(
            sidebar, 
            text=f"@{self.username}", 
            font=("Arial", 20, "bold")
        )
        profile_label.pack(pady=20)
        
        # Navigation buttons
        buttons = [
            ("Follow User", self.follow_user),
            ("Unfollow User", self.unfollow_user),
            ("View Followers", self.view_followers),
            ("View Following", self.view_following),
            ("Visualize Network", self.update_visualization),
            ("Change User", self.create_user_selection),
            ("Save Profile", self.save_all_users)
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(sidebar, text=text, command=command)
            btn.pack(pady=5, fill="x")
        
        # Visualization frame
        self.canvas_frame = ctk.CTkFrame(main_frame)
        self.canvas_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)
        
        # Initial network visualization
        self.update_visualization()
    
    def unfollow_user(self):
        """Open a dialog to unfollow a user."""
        current_following = list(self.network.following)
        
        # Create unfollow dialog
        unfollow_window = ctk.CTkToplevel(self.root)
        unfollow_window.title("Unfollow User")
        unfollow_window.geometry("300x200")
        
        ctk.CTkLabel(unfollow_window, text="Select a user to unfollow:").pack(pady=10)
        
        user_dropdown = ctk.CTkComboBox(
            unfollow_window, 
            values=current_following, 
            state="readonly"
        )
        user_dropdown.pack(pady=10)
        
        def confirm_unfollow():
            user = user_dropdown.get()
            if user:
                if self.network.unfollow(user):
                    # Remove follower from the unfollowed user's followers
                    if user in self.all_users_data:
                        followers = self.all_users_data[user].get("followers", [])
                        if self.username in followers:
                            followers.remove(self.username)
                        self.all_users_data[user]["followers"] = followers
                    
                    messagebox.showinfo("Success", f"You are no longer following {user}")
                    self.save_all_users()
                    self.update_visualization()
                    unfollow_window.destroy()
                else:
                    messagebox.showerror("Error", "Could not unfollow the user")
        
        ctk.CTkButton(unfollow_window, text="Unfollow", command=confirm_unfollow).pack(pady=10)

    def synchronize_follow(self, follower, followed):
        """Synchronize following and followers between two users."""
        # Ensure the data structure exists for both users
        if followed not in self.all_users_data:
            self.all_users_data[followed] = {"following": [], "followers": []}
        
        # Add follower to the followed user's followers
        if follower not in self.all_users_data[followed].get("followers", []):
            self.all_users_data[followed]["followers"].append(follower)
        
        # Add followed to the follower's following list
        if followed not in self.all_users_data[follower].get("following", []):
            self.all_users_data[follower]["following"].append(followed)
        
        # Save updated network data
        self.save_all_users()

    def follow_user(self):
        """Open a dialog to follow a user."""
        available_users = list(self.network.all_users - self.network.following - {self.username})
        
        # Create follow dialog
        follow_window = ctk.CTkToplevel(self.root)
        follow_window.title("Follow User")
        follow_window.geometry("300x200")
        
        ctk.CTkLabel(follow_window, text="Select a user to follow:").pack(pady=10)
        
        user_dropdown = ctk.CTkComboBox(
            follow_window, 
            values=available_users, 
            state="readonly"
        )
        user_dropdown.pack(pady=10)
        
        def confirm_follow():
            user = user_dropdown.get()
            if user:
                if self.network.follow(user):
                    self.synchronize_follow(self.username, user)
                    messagebox.showinfo("Success", f"You are now following {user}")
                    self.save_all_users()
                    self.update_visualization()
                    follow_window.destroy()
                else:
                    messagebox.showerror("Error", "Could not follow the user")
        
        ctk.CTkButton(follow_window, text="Follow", command=confirm_follow).pack(pady=10)

    def view_followers(self):
        """Display a list of followers."""
        followers = list(self.network.followers)
        followers_str = "\n".join(followers) if followers else "No followers yet."
        messagebox.showinfo("Followers", followers_str)

    def view_following(self):
        """Display a list of users the current user is following."""
        following = list(self.network.following)
        following_str = "\n".join(following) if following else "You are not following anyone yet."
        messagebox.showinfo("Following", following_str)

    def update_visualization(self):
        """Visualize the social network graph."""
        # Clear existing canvas
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        # Create a directed graph
        graph = nx.DiGraph()
        
        # Add nodes and edges
        for user, data in self.all_users_data.items():
            graph.add_node(user)
            for followed_user in data.get("following", []):
                graph.add_edge(user, followed_user)
        
        # Draw the graph
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(graph)
        nx.draw(
            graph, pos, with_labels=True, node_color="skyblue", 
            node_size=2000, font_size=10, font_weight="bold", ax=ax
        )
        
        # Embed the graph in the Tkinter canvas
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_user_selection(self):
        """Create a user selection window."""
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # User selection frame
        selection_frame = ctk.CTkFrame(self.root)
        selection_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        ctk.CTkLabel(
            selection_frame, 
            text="Select or Create a User", 
            font=("Arial", 20, "bold")
        ).pack(pady=20)
        
        # Dropdown for existing users
        existing_users = list(self.all_users_data.keys())
        user_dropdown = ctk.CTkComboBox(
            selection_frame, 
            values=existing_users, 
            state="readonly"
        )
        user_dropdown.pack(pady=10)
        
        def select_user():
            username = user_dropdown.get()
            if username:
                self.username = username
                self.network = SocialNetwork(username)
                self.network.following = set(self.all_users_data[username].get("following", []))
                self.network.followers = set(self.all_users_data[username].get("followers", []))
                self.create_dashboard()
        
        ctk.CTkButton(selection_frame, text="Select User", command=select_user).pack(pady=10)
        
        # Create new user
        def create_user():
            username = simpledialog.askstring("Create User", "Enter a new username:")
            if username and username not in self.all_users_data:
                self.username = username
                self.network = SocialNetwork(username)
                self.all_users_data[username] = {"following": [], "followers": []}
                self.save_all_users()
                self.create_dashboard()
            elif username:
                messagebox.showerror("Error", "Username already exists")
        
        ctk.CTkButton(selection_frame, text="Create New User", command=create_user).pack(pady=10)

    def load_all_users(self):
        """Load all users' data from a JSON file."""
        if os.path.exists("users_data.json"):
            with open("users_data.json", "r") as file:
                self.all_users_data = json.load(file)

    def save_all_users(self):
        """Save all users' data to a JSON file."""
        with open("users_data.json", "w") as file:
            json.dump(self.all_users_data, file, indent=4)

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

# Application entry point
if __name__ == "__main__":
    app = SocialNetworkApp()
    app.run()