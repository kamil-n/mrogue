import logging, random;

def roll( dieString, crit = False ):
    separatorIndex = dieString.index( 'd' );
    numDie = int( dieString[:separatorIndex] );
    typeDie = dieString[separatorIndex+1:];
    if crit:
        logging.warn( 'WE HAVE A FUCKING CRIT!!!' );
        numDie *= 2;
        dieString = str( numDie ) + dieString[separatorIndex:];
    modifier = 0;
    modifierIndex = -1;
    if '-' in typeDie:
        modifierIndex = typeDie.index( '-' );
    elif '+' in typeDie:
        modifierIndex = typeDie.index( '+' );
    if not modifierIndex == -1:
        modifier = int( typeDie[modifierIndex:] );
        typeDie = int( typeDie[:modifierIndex] );
    else:
        typeDie = int( typeDie );
    rollResult = 0;
    resultString = '';
    for i in range( numDie ):
        roll = random.randint( 1, typeDie );
        resultString += str( roll ) + '+';
        rollResult += roll;
    rollResult += modifier;
    resultString = resultString[:-1];
    if rollResult < 1:
        rollResult = 1;
    if modifier < 0:
        resultString += str(modifier);
    elif modifier > 0:
        resultString += '+' + str( modifier ); 
    logging.info( 'rolling %s: %s = %d' % ( dieString, resultString, rollResult ) );
    return rollResult;