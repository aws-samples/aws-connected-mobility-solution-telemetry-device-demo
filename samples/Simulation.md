# Setting up for Random Simulation without replay data

When captured, simulated, reference or other data is not available, it is straightforward to configure the `telemetryThing` to use randomized telemetry. This guide describes how to set that up and also shows the use of dot notation for property names.

To accomplish this, setup a generator script that emits a single row of header information, which gives the property names for the final payload (optionally using dot notation) and redirect the output to a named pipe. The `telemetryThing` can then read from this pipe and send the data.  This gives a great deal of control over the simulation and randomization of the data.

### Step 1 - Modify and copy the generator script

Open the file `gen.py` and modify as needed. As written, the FIRST metric is the timestamp in milliseconds that will be part of each record. The `telemetryThing` will also use this value for delay loop timing, so the `gen.py` script incorporates a matching delay between emission of records.

Each parameter can have a `method` for randomization.  In the example, `Timestamp(ms)` is randomized with a normal distribution with a mean of 5 seconds and a standard of deviation of 1 second.

Additional parameters can be added to the `metrics` table below `Timestamp(ms)`. While any method can be used to randomize, the `np.random.choice` method is handy to choose among a set of options, this set can be a single value to create a constant.

In the example, note the measure names `e.t` and `e.h`. If the payload_strategy is set to DotLabelledPayload, these will be expanded to create a message payload like

```json
{
    "Timestamp(ms)": 12345.6789,
    "e": {
        "t": 18.9,
        "h": 34.5
    },
    "l": "{c={o=AT&T, a=[{i=1704630, l=56986, c=310, n=410}]}"
}
```

Run the `gen.py` script a few times in the terminal to ensure the data is being created as desired. It may be helpful to copy the script to the same directory as `telemetryThing`. You may also need to set the `execute` bit (`chmod +x gen.py`).

### Step 2 - Create a named pipe

Create a fifo to buffer the data from the generator to `telemetryThing`

```bash
mkfifo generated_data
```


### Step 3 - Configure `telemetryThing`

Modify the `Config.py` file to 

1. read from the fifo with the proper formatting
2. use the `Timestamp(ms)` column for timing
3. use the `DotLabelledPayload` strategy

```python
state = {
    'file': 'file:///generated_data',
    'record_separator': '\t',
    'quote_records': True,

    #
    # Timestamp handling
    #
    'time_col_name': 'Timestamp(ms)',   # column name to use for time        
    'time_scale': 1000.0,               # units/second -- e.g. 1000.0 means stamps in milliseconds

    # Select a Strategy from MessagePayload.py to define how to format a payload from the record
    'payload_strategy': 'DotLabelledPayload',
    
    # Topic to publish messages, different payload_strategies may need different templates using local vars
    'topic_name': "dt/{deviceid}",
    
    # what to do at the end of the file... 'stop' or 'repeat'
    'at_end': 'repeat',
}   
```

**NB-** Since one of the data field options (`l`) has embedded commas (','), we use tab ('\t') as a record separator.

### Step 4 - GO!

Start the `telemetryThing` with

```bash
python3 ./telemetryThing.py -e $ENDPOINT -r root.ca.pem -c $CERT -k $KEY -n 'vivacious'
```

See the main [README.md](https://github.com/aws-samples/aws-connected-mobility-solution-telemetry-device-demo/blob/main/README.md) for details on thing creation, certificate download, and environment variable setup.

And start the generator to populate the pipe

```bash
samples/gen.py > generated_data
```

**NB-** Generally start the generator before starting the telemetry device, however, setting the 'at_end' behavior to 'repeat' will ensure the device will pick up the generated data. When the device ends, the pipe will be 'broken' and the generator will need to be restarted.
