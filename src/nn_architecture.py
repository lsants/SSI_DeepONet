# ------------------- Define Neural Network architecture -------------------
import torch.nn as nn

nodes_config = [96, 96, 96, 96, 96, 96, 96]


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.dropout = nn.Dropout(0.2)
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(4, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 96),
            # nn.Dropout(p=0.5),
            nn.ReLU(),
            nn.Linear(96, 1),
            # nn.Dropout(p=0.5),
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits
