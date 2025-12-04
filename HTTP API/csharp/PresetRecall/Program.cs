using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;

/// <summary>
/// This program demonstrates how to make an HTTP API call to a PTZOptics camera
/// to recall a preset position using Digest Authentication.
/// It prompts the user for connection details and sends a GET request
/// to the camera's CGI endpoint to trigger the preset recall.
/// </summary>
class Program
{
    static async Task Main(string[] args)
    {
        // Get connection details once
        Console.Write("Enter IP Address (e.g., 192.168.1.50): ");
        string ipAddress = Console.ReadLine()?.Trim() ?? string.Empty;

        Console.Write("Enter Username: ");
        string username = Console.ReadLine()?.Trim() ?? string.Empty;

        Console.Write("Enter Password: ");
        string password = Console.ReadLine()?.Trim() ?? string.Empty;

        // Configure the Handler for Digest Authentication
        var handler = new HttpClientHandler
        {
            Credentials = new NetworkCredential(username, password)
        };

        using (var client = new HttpClient(handler))
        {
            while (true)
            {
                Console.Write("\nEnter Preset Number (or 'exit' to quit): ");
                string input = Console.ReadLine()?.Trim() ?? string.Empty;

                if (input.ToLower() == "exit")
                {
                    Console.WriteLine("Exiting...");
                    break;
                }

                if (string.IsNullOrWhiteSpace(input))
                {
                    Console.WriteLine("Please enter a valid preset number.");
                    continue;
                }

                // Construct the URL
                string url = $"http://{ipAddress}/cgi-bin/ptzctrl.cgi?ptzcmd&poscall&{input}";

                Console.WriteLine($"\nTargeting: {url}");
                Console.WriteLine("Sending request...");

                try
                {
                    // Send the GET request
                    HttpResponseMessage response = await client.GetAsync(url);

                    // Output Results
                    if (response.IsSuccessStatusCode)
                    {
                        Console.WriteLine("Success! Command sent.");
                        Console.WriteLine($"Status Code: {response.StatusCode}");

                        string content = await response.Content.ReadAsStringAsync();
                        if (!string.IsNullOrWhiteSpace(content))
                        {
                            Console.WriteLine($"Response: {content}");
                        }
                    }
                    else
                    {
                        Console.WriteLine($"Error: The camera returned status code {response.StatusCode}");
                        Console.WriteLine($"Reason: {response.ReasonPhrase}");
                    }
                }
                catch (HttpRequestException e)
                {
                    Console.WriteLine($"\nNetwork Error: {e.Message}");
                }
                catch (Exception e)
                {
                    Console.WriteLine($"\nAn unexpected error occurred: {e.Message}");
                }
            }
        }
    }
}
